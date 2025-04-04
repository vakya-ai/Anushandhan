from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
from datetime import datetime
from app.core.database import init_db, get_database

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AcademAI API")

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
async def generate_paper_content(topic, sections, word_count, source_type=None, source_url=None):
    """Generate paper content based on the topic and optional source URL."""
    try:
        # If GitHub URL is provided, use GitHub repository analysis
        if source_type == "github" and source_url:
            from app.services.paper_generator import GitHubPaperGenerator
            generator = GitHubPaperGenerator()
            return await generator.generate_research_paper(topic, source_url, sections)
        else:
            # Default generation for other cases (basic template)
            paper_content = f"""# {topic}

## Abstract
This paper explores {topic} in depth, providing insights and analysis.

"""
            # Add each section
            for section in sections:
                paper_content += f"\n## {section}\n"
                paper_content += f"Content for {section} related to {topic}. This section would typically contain relevant information about {topic}.\n"
            
            return paper_content
    except Exception as e:
        logger.error(f"Error in generate_paper_content: {str(e)}")
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

# Background task to generate paper
async def background_paper_generation(document_id, request_data):
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
            request_data.get("sourceUrl")
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
            request.dict()
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