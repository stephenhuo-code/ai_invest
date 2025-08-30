"""
Database infrastructure package.

Contains database models, connections, and repository implementations.
"""

from .models import Base, NewsArticle, AnalysisResult, VectorEmbedding
from .connection import DatabaseManager, get_db_manager, init_database, get_repository
from .unified_repository import UnifiedDatabaseRepository

__all__ = [
    "Base",
    "NewsArticle", 
    "AnalysisResult",
    "VectorEmbedding",
    "DatabaseManager",
    "get_db_manager",
    "init_database",
    "get_repository",
    "UnifiedDatabaseRepository"
]