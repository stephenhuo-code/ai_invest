"""
AnalysisResult domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    SENTIMENT = "sentiment"
    TOPICS = "topics"
    STOCKS = "stocks"
    SUMMARY = "summary"
    CLASSIFICATION = "classification"


@dataclass
class AnalysisResult:
    """Domain entity for analysis results."""
    article_id: int
    analysis_type: AnalysisType
    model_name: str
    result: Dict[str, Any]
    model_version: Optional[str] = None
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    tokens_used: int = 0
    
    # Database fields
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.analysis_type, str):
            self.analysis_type = AnalysisType(self.analysis_type)
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence analysis."""
        return self.confidence_score >= 0.8
    
    @property
    def sentiment(self) -> Optional[str]:
        """Get sentiment if this is a sentiment analysis."""
        if self.analysis_type == AnalysisType.SENTIMENT:
            return self.result.get('sentiment')
        return None
    
    @property
    def topics(self) -> Optional[list]:
        """Get topics if this is a topic analysis."""
        if self.analysis_type == AnalysisType.TOPICS:
            return self.result.get('topics', [])
        return None
    
    @property
    def stocks(self) -> Optional[list]:
        """Get stock mentions if this is a stock analysis."""
        if self.analysis_type == AnalysisType.STOCKS:
            return self.result.get('stocks', [])
        return None