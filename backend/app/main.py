# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import db
from app.models.document import Document, ProcessingStatus
from app.services.github_processor import GitHubProcessor
from app.services.content_generator import ContentGenerator
from app.services.ieee_formatter import IEEEFormatter
from typing import Dict
import asyncio
import aioredis
from app.core.config import settings

app = FastAPI(title="AI Research Paper Generator")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
github_processor = GitHubProcessor()
content_generator = ContentGenerator()
ieee_formatter = IEEEFormatter()

@app.on_event("startup")
async def startup_db_client():
    await db.connect_db()
    app.state.redis = await aioredis.from_url(settings.REDIS_URL)

@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_db()
    await app.state.redis.close()

async def get_document_by_id(document_id: str) -> Document:
    document = await db.engine.find_one(Document, Document.id == document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.post("/api/upload/github")
async def process_github_repo(repository_url: str, branch: str = "main"):
    try:
        # Create document record
        document = Document(
            title="Untitled Research Paper",
            user_id="system",  # Replace with actual user ID in production
            input_type="github",
            repository_metadata={
                "url": repository_url,
                "branch": branch,
                "commit_hash": "",
                "total_files": 0
            }
        )
        await db.engine.save(document)

        # Start processing in background
        asyncio.create_task(process_document(document.id, repository_url, branch))

        return {"document_id": str(document.id), "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/upload/folder")
async def process_folder(file: UploadFile = File(...)):
    try:
        # Create document record
        document = Document(
            title="Untitled Research Paper",
            user_id="system",
            input_type="folder",
            file_metadata={
                "name": file.filename,
                "path": "",
                "content_type": file.content_type,
                "size": 0
            }
        )
        await db.engine.save(document)

        # Process file content
        content = await file.read()
        
        # Start processing in background
        asyncio.create_task(process_folder_content(document.id, content))

        return {"document_id": str(document.id), "status": "processing"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/status/{document_id}")
async def get_status(document_id: str):
    document = await get_document_by_id(document_id)
    return {
        "status": document.status,
        "error_message": document.error_message if document.status == ProcessingStatus.FAILED else None
    }

@app.get("/api/document/{document_id}")
async def get_document(document_id: str):
    document = await get_document_by_id(document_id)
    if document.status != ProcessingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Document processing not completed")
    return document

async def process_document(document_id: str, repository_url: str, branch: str):
    try:
        # Update status
        document = await get_document_by_id(document_id)
        document.status = ProcessingStatus.PROCESSING
        await db.engine.save(document)
        
        # Rest of your processing logic here
        
    except Exception as e:
        # Update document status to failed
        document = await get_document_by_id(document_id)
        document.status = ProcessingStatus.FAILED
        document.error_message = str(e)
        await db.engine.save(document)
        raise