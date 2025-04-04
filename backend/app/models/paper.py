from enum import Enum
from typing import Dict, List, Optional, Any
from odmantic import Model
from datetime import datetime
from odmantic import Field

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Model):
    title: str
    user_id: str
    input_type: str  # "github" or "folder"
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    
    # Metadata fields
    repository_metadata: Optional[Dict[str, Any]] = None
    file_metadata: Optional[Dict[str, Any]] = None
    
    # Paper sections
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methodology: Optional[str] = None
    literature_review: Optional[str] = None
    results: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None
    references: Optional[List[str]] = None
    
    # Generated content
    code_chunks: Optional[List[Dict[str, Any]]] = None
    paper_html: Optional[str] = None
    paper_pdf_url: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class Config:
    collection = "documents"