"""
VectorDocument domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class VectorSourceType(Enum):
    """Source types for vector documents."""
    NEWS = "news"
    ANALYSIS = "analysis"
    REPORT = "report"
    EXTERNAL = "external"


@dataclass
class VectorDocument:
    """Domain entity for vector documents."""
    source_type: VectorSourceType
    source_id: str
    content_hash: str
    embedding: List[float]
    embedding_model: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    dimension: Optional[int] = None
    
    # Database fields
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.source_type, str):
            self.source_type = VectorSourceType(self.source_type)
        
        # Set dimension from embedding if not provided
        if self.dimension is None and self.embedding:
            self.dimension = len(self.embedding)
    
    @property
    def is_valid(self) -> bool:
        """Check if the vector document is valid."""
        return (
            bool(self.embedding) and
            len(self.embedding) > 0 and
            bool(self.content_hash) and
            bool(self.source_id)
        )
    
    def similarity_to(self, other_embedding: List[float]) -> float:
        """Calculate cosine similarity to another embedding."""
        if not self.embedding or not other_embedding:
            return 0.0
        
        if len(self.embedding) != len(other_embedding):
            return 0.0
        
        # Simple dot product for cosine similarity (assuming normalized vectors)
        dot_product = sum(a * b for a, b in zip(self.embedding, other_embedding))
        return max(0.0, min(1.0, dot_product))  # Clamp to [0, 1]


@dataclass
class VectorSearchResult:
    """Result from vector similarity search."""
    document: VectorDocument
    similarity_score: float
    distance: float = 0.0
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert similarity to distance if not provided
        if self.distance == 0.0:
            self.distance = 1.0 - self.similarity_score