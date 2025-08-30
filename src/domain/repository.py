"""
Domain repository interfaces.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities.news_article import NewsArticle
from .entities.analysis_result import AnalysisResult
from .entities.vector_document import VectorDocument, VectorSearchResult


class DataRepository(ABC):
    """Abstract repository interface for data operations."""
    
    # News operations
    @abstractmethod
    async def save_news(self, news: NewsArticle) -> NewsArticle:
        """Save a news article."""
        pass
    
    @abstractmethod
    async def find_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[NewsArticle]:
        """Find recent news articles."""
        pass
    
    @abstractmethod
    async def find_news_by_id(self, news_id: int) -> Optional[NewsArticle]:
        """Find news article by ID."""
        pass
    
    # Analysis operations
    @abstractmethod
    async def save_analysis(self, analysis: AnalysisResult) -> AnalysisResult:
        """Save an analysis result."""
        pass
    
    @abstractmethod
    async def find_analysis_by_news_id(self, news_id: int) -> List[AnalysisResult]:
        """Find analysis results for a news article."""
        pass
    
    @abstractmethod
    async def find_recent_analysis(self, days: int = 7, limit: Optional[int] = None) -> List[AnalysisResult]:
        """Find recent analysis results."""
        pass
    
    # Vector operations
    @abstractmethod
    async def save_vector(self, vector_doc: VectorDocument) -> VectorDocument:
        """Save a vector document."""
        pass
    
    @abstractmethod
    async def search_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Perform vector similarity search."""
        pass
    
    @abstractmethod
    async def get_vector_count(self) -> int:
        """Get total number of vectors stored."""
        pass
    
    # Health check
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the repository is healthy."""
        pass