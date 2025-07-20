import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
import jwt
from datetime import datetime
from app.core.database import init_db, get_database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AcademAI API")

# Import all routers
from app.api.research_generator import router as research_router
from app.api.auth import router as auth_router
from app.api.chats import router as chats_router
from app.api.papers import router as papers_router

# Include all routers
app.include_router(research_router, prefix="/api/research")
app.include_router(auth_router)  # Auth router already has /api/auth prefix
app.include_router(chats_router)  # Chats router already has /api/chats prefix
app.include_router(papers_router)  # Papers router already has /api/papers prefix

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
db = None

@app.on_event("startup")
async def startup_db_client():
    global db
    db = await init_db()
    logger.info("Successfully connected to MongoDB database: academai")
    
    # Create necessary indexes if they don't exist
    try:
        # User collection indexes
        await db.users.create_index("googleId", unique=True)
        await db.users.create_index("email")
        
        # Sessions collection indexes
        await db.sessions.create_index([("userId", 1), ("active", 1)])
        
        # Activities collection indexes
        await db.user_activities.create_index([("userId", 1), ("timestamp", -1)])
        
        # Chats collection indexes
        await db.chats.create_index([("userId", 1), ("id", 1)])
        
        # Paper activities collection indexes
        await db.paper_activities.create_index([("userId", 1), ("documentId", 1)])
        await db.paper_activities.create_index([("userId", 1), ("type", 1), ("timestamp", -1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating database indexes: {str(e)}")

# Define request models
class PaperRequest(BaseModel):
    topic: str
    sections: List[str]
    wordCount: int
    sourceType: Optional[str] = None
    sourceUrl: Optional[str] = None

# Define response models
class PaperResponse(BaseModel):
    status: str
    document_id: Optional[str] = None
    message: Optional[str] = None
    paper: Optional[str] = None

# Storage for background tasks
paper_jobs = {}

# Simulate paper generation
async def generate_paper_content(topic, sections, word_count, source_type=None, source_url=None, user_id=None):
    """Generate paper content based on the topic and optional source URL."""
    try:
        # Import the ResearchPaperGenerator from research_generator.py
        from app.api.research_generator import ResearchPaperGenerator
        
        # Create an instance of the research paper generator
        generator = ResearchPaperGenerator()
        
        # Generate the paper using the generator
        paper_result = await generator.generate_research_paper(
            topic=topic,
            sections=sections,
            word_count=word_count,
            repo_url=source_url if source_type == "github" else None
        )
        
        # If user is authenticated, track the paper generation
        if user_id:
            await track_paper_generation(
                user_id=user_id,
                document_id=str(uuid.uuid4()),
                topic=topic,
                sections=sections,
                word_count=word_count,
                source_type=source_type,
                source_url=source_url
            )
        
        # Return the full paper content
        return paper_result.get("Full Paper", "Error generating paper content")
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error in generate_paper_content: {str(e)}")
        logger.error(error_traceback)
        # Return a basic paper with error information for debugging
        return f"""# Error Generating Complete Paper for {topic}

## Issues Encountered
Unfortunately, we encountered an error while generating the full paper: {str(e)}

## Basic Content
Here is the basic content we can provide:

### Abstract
This paper was intended to explore {topic} in depth.

### Introduction
The introduction would provide background on {topic}.
"""

async def track_paper_generation(user_id, document_id, topic, sections, word_count, source_type, source_url):
    """Track paper generation in the database"""
    try:
        if not db:
            logger.warning("Database not initialized, skipping paper tracking")
            return
            
        # Store paper generation activity
        await db.paper_activities.insert_one({
            "userId": user_id,
            "documentId": document_id,
            "topic": topic,
            "type": "generation",
            "timestamp": datetime.now(),
            "details": {
                "sections": sections,
                "wordCount": word_count,
                "sourceType": source_type,
                "sourceUrl": source_url,
            }
        })
        
        # Update user's papers generated count
        await db.users.update_one(
            {"googleId": user_id},
            {"$inc": {"papersGenerated": 1}}
        )
    except Exception as e:
        logger.error(f"Error tracking paper generation: {str(e)}")
        # Don't raise the exception, just log it

# Background task to generate paper
async def background_paper_generation(document_id, request_data, user_id=None):
    try:
        # Get database collection
        papers_collection = db.get_collection("papers")
        
        # Update status to processing
        await papers_collection.update_one(
            {"_id": document_id},
            {"$set": {"status": "processing", "updated_at": datetime.now()}}
        )
        
        # Generate paper content with source URL if available
        paper_content = await generate_paper_content(
            request_data["topic"],
            request_data["sections"],
            request_data["wordCount"],
            request_data.get("sourceType"),
            request_data.get("sourceUrl"),
            user_id
        )
        
        # Update database with completed paper
        await papers_collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": "completed",
                    "paper_content": paper_content,
                    "updated_at": datetime.now()
                }
            }
        )
        
        # Update in-memory storage
        paper_jobs[document_id]["status"] = "success"
        paper_jobs[document_id]["paper"] = paper_content
        
    except Exception as e:
        logger.error(f"Error generating paper: {str(e)}")
        # Update database with error status
        await papers_collection.update_one(
            {"_id": document_id},
            {"$set": {"status": "error", "error": str(e), "updated_at": datetime.now()}}
        )
        
        # Update in-memory storage
        paper_jobs[document_id]["status"] = "error"
        paper_jobs[document_id]["message"] = str(e)

@app.post("/api/research/generate-paper", response_model=PaperResponse)
async def generate_paper(request: PaperRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received paper generation request for topic: {request.topic}")
        
        # Extract user ID from request if available
        user_id = None
        try:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.replace("Bearer ", "")
                decoded_token = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded_token.get("sub")
        except Exception as e:
            logger.warning(f"Error extracting user ID from request: {str(e)}")
        
        # Validate GitHub URL if provided
        if request.sourceType == "github" and request.sourceUrl:
            from app.utils.url_validator import URLValidator
            if not URLValidator.is_valid_github_url(request.sourceUrl):
                raise ValueError("Invalid GitHub repository URL format")
        
        # Create a unique ID for this paper request
        document_id = str(uuid.uuid4())
        
        # Store initial data in MongoDB
        papers_collection = db.get_collection("papers")
        await papers_collection.insert_one({
            "_id": document_id,
            "topic": request.topic,
            "sections": request.sections,
            "word_count": request.wordCount,
            "source_type": request.sourceType,
            "source_url": request.sourceUrl,
            "user_id": user_id,
            "status": "queued",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        # Add to in-memory storage
        paper_jobs[document_id] = {
            "status": "processing",
            "paper": None,
            "message": None
        }
        
        # Start background task to generate the paper
        background_tasks.add_task(
            background_paper_generation,
            document_id,
            request.dict(),
            user_id
        )
        
        return PaperResponse(
            status="processing",
            document_id=document_id
        )
        
    except Exception as e:
        logger.error(f"Error starting paper generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/research/paper/{document_id}", response_model=PaperResponse)
async def get_paper_status(document_id: str):
    # Check in-memory storage first (faster)
    if document_id in paper_jobs:
        job = paper_jobs[document_id]
        return PaperResponse(
            status=job["status"],
            message=job["message"],
            paper=job["paper"]
        )
    
    # If not found in memory, check database
    papers_collection = db.get_collection("papers")
    paper_doc = await papers_collection.find_one({"_id": document_id})
    
    if not paper_doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper_doc["status"] == "completed":
        return PaperResponse(
            status="success",
            paper=paper_doc["paper_content"]
        )
    elif paper_doc["status"] == "error":
        return PaperResponse(
            status="error",
            message=paper_doc.get("error", "Unknown error")
        )
    else:
        return PaperResponse(
            status="processing",
            document_id=document_id
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}