# backend/app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "ai_paper_generator"
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()

# backend/app/models/document.py
from datetime import datetime
from typing import List, Optional
from odmantic import Model, EmbeddedModel
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileMetadata(EmbeddedModel):
    name: str
    path: str
    content_type: str
    size: int

class RepositoryMetadata(EmbeddedModel):
    url: str
    branch: str
    commit_hash: str
    total_files: int

class PaperSection(EmbeddedModel):
    title: str
    content: str
    section_type: str
    order: int

class Document(Model):
    title: str
    user_id: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    input_type: str  # "github" or "folder"
    file_metadata: Optional[FileMetadata]
    repository_metadata: Optional[RepositoryMetadata]
    sections: List[PaperSection] = []
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    error_message: Optional[str]
    
    class Config:
        collection = "documents"

# backend/app/core/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    engine: AIOEngine = None

    async def connect_db(self):
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.engine = AIOEngine(
            client=self.client,
            database=settings.DATABASE_NAME
        )

    async def close_db(self):
        if self.client:
            await self.client.close()

    async def get_engine(self) -> AIOEngine:
        return self.engine

db = Database()