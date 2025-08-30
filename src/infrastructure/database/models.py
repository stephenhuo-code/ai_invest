"""
SQLAlchemy models for AI Invest platform.

Database models for PostgreSQL with pgvector support.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Create the base class
Base = declarative_base()


class NewsArticle(Base):
    """News article database model."""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    title = Column(String(1024), nullable=False)
    content = Column(Text)
    content_hash = Column(String(64), nullable=False, index=True)
    source = Column(String(256), nullable=False, index=True)
    author = Column(String(512))
    
    # Timestamps
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing tracking
    processing_status = Column(String(32), nullable=False, default='pending', index=True)
    processing_attempts = Column(Integer, default=0)
    last_processed_at = Column(DateTime)
    
    # Metadata
    article_metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"


class AnalysisResult(Base):
    """Analysis result database model."""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False, index=True)  # Foreign key to news_articles
    
    # Analysis details
    analysis_type = Column(String(64), nullable=False, index=True)
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(64))
    
    # Results
    result = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=0.0)
    
    # Performance metrics
    processing_time_ms = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, article_id={self.article_id}, type='{self.analysis_type}')>"


class VectorEmbedding(Base):
    """Vector embedding database model using pgvector."""
    __tablename__ = 'vector_embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source reference
    source_type = Column(String(64), nullable=False, index=True)  # 'news', 'analysis', etc.
    source_id = Column(String(128), nullable=False, index=True)   # ID of source document
    content_hash = Column(String(64), nullable=False, index=True)
    
    # Vector data
    # Note: In a real implementation, this would use pgvector's vector type
    # For now, we'll use JSON to store the embedding array
    embedding = Column(JSON, nullable=False)  # Should be pgvector.vector type in production
    embedding_model = Column(String(128), nullable=False)
    dimension = Column(Integer, nullable=False)
    
    # Metadata
    vector_metadata = Column(JSON, default=dict)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VectorEmbedding(id={self.id}, source_type='{self.source_type}', source_id='{self.source_id}')>"


# Create all tables function
def create_tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Drop all tables function  
def drop_tables(engine):
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)