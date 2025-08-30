"""
NewsArticle domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ProcessingStatus(Enum):
    """Processing status for news articles."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class NewsArticle:
    """Domain entity for news articles."""
    url: str
    title: str
    content: str
    content_hash: str
    source: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_attempts: int = 0
    last_processed_at: Optional[datetime] = None
    
    # Database fields
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.processing_status, str):
            self.processing_status = ProcessingStatus(self.processing_status)
    
    def mark_processing(self) -> None:
        """Mark the article as being processed."""
        self.processing_status = ProcessingStatus.PROCESSING
        self.processing_attempts += 1
        self.last_processed_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark the article as successfully processed."""
        self.processing_status = ProcessingStatus.COMPLETED
        self.last_processed_at = datetime.utcnow()
    
    def mark_failed(self) -> None:
        """Mark the article as failed to process."""
        self.processing_status = ProcessingStatus.FAILED
        self.last_processed_at = datetime.utcnow()
    
    def should_retry(self, max_attempts: int = 3) -> bool:
        """Check if the article should be retried for processing."""
        return (
            self.processing_status == ProcessingStatus.FAILED and
            self.processing_attempts < max_attempts
        )
    
    @property
    def is_processed(self) -> bool:
        """Check if the article has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    @property
    def summary(self) -> str:
        """Get a short summary of the article."""
        max_length = 200
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."