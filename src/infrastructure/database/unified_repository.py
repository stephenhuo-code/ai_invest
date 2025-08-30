"""
Unified Database Repository implementation.

Implements the simplified DataRepository interface using PostgreSQL + pgvector.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, desc, and_
from sqlalchemy.orm import selectinload

from ...domain.repository import DataRepository, VectorSearchResult
from ...domain.entities.news_article import NewsArticle, ProcessingStatus
from ...domain.entities.analysis_result import AnalysisResult, AnalysisType
from ...domain.entities.vector_document import VectorDocument, VectorSourceType
from .models import NewsArticle as NewsArticleModel
from .models import AnalysisResult as AnalysisResultModel
from .models import VectorEmbedding as VectorEmbeddingModel
from .connection import get_db_manager


class UnifiedDatabaseRepository(DataRepository):
    """
    Unified implementation of the DataRepository interface.
    
    Combines news, analysis, and vector operations into a single repository.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_session(self):
        """Get database session context manager."""
        db_manager = get_db_manager()
        return db_manager.get_async_session()
    
    # News operations
    async def save_news(self, news: NewsArticle) -> NewsArticle:
        """Save a news article."""
        async with self._get_session() as session:
            try:
                # Convert domain entity to database model
                news_model = NewsArticleModel(
                    url=news.url,
                    title=news.title,
                    content=news.content,
                    content_hash=news.content_hash,
                    source=news.source,
                    author=news.author,
                    published_at=news.published_at,
                    fetched_at=news.fetched_at,
                    article_metadata=news.metadata,
                    processing_status=news.processing_status.value,
                    processing_attempts=news.processing_attempts,
                    last_processed_at=news.last_processed_at
                )
                
                session.add(news_model)
                await session.commit()
                await session.refresh(news_model)
                
                # Convert back to domain entity
                return self._news_model_to_entity(news_model)
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save news article: {str(e)}")
                raise
    
    async def find_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[NewsArticle]:
        """Find recent news articles."""
        async with self._get_session() as session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                query = select(NewsArticleModel).where(
                    NewsArticleModel.created_at >= cutoff_date
                ).order_by(desc(NewsArticleModel.created_at))
                
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                news_models = result.scalars().all()
                
                return [self._news_model_to_entity(model) for model in news_models]
                
            except Exception as e:
                self.logger.error(f"Failed to find recent news: {str(e)}")
                raise
    
    async def find_news_by_id(self, news_id: int) -> Optional[NewsArticle]:
        """Find news article by ID."""
        async with self._get_session() as session:
            try:
                query = select(NewsArticleModel).where(NewsArticleModel.id == news_id)
                result = await session.execute(query)
                news_model = result.scalar_one_or_none()
                
                if news_model:
                    return self._news_model_to_entity(news_model)
                return None
                
            except Exception as e:
                self.logger.error(f"Failed to find news by ID {news_id}: {str(e)}")
                raise
    
    # Analysis operations
    async def save_analysis(self, analysis: AnalysisResult) -> AnalysisResult:
        """Save an analysis result."""
        async with self._get_session() as session:
            try:
                # Convert domain entity to database model
                analysis_model = AnalysisResultModel(
                    article_id=analysis.article_id,
                    analysis_type=analysis.analysis_type.value,
                    model_name=analysis.model_name,
                    model_version=analysis.model_version,
                    result=analysis.result,
                    confidence_score=analysis.confidence_score,
                    processing_time_ms=analysis.processing_time_ms,
                    tokens_used=analysis.tokens_used
                )
                
                session.add(analysis_model)
                await session.commit()
                await session.refresh(analysis_model)
                
                # Convert back to domain entity
                return self._analysis_model_to_entity(analysis_model)
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save analysis result: {str(e)}")
                raise
    
    async def find_analysis_by_news_id(self, news_id: int) -> List[AnalysisResult]:
        """Find analysis results for a specific news article."""
        async with self._get_session() as session:
            try:
                query = select(AnalysisResultModel).where(
                    AnalysisResultModel.article_id == news_id
                ).order_by(desc(AnalysisResultModel.created_at))
                
                result = await session.execute(query)
                analysis_models = result.scalars().all()
                
                return [self._analysis_model_to_entity(model) for model in analysis_models]
                
            except Exception as e:
                self.logger.error(f"Failed to find analysis for news ID {news_id}: {str(e)}")
                raise
    
    async def find_recent_analysis(self, days: int = 7, limit: Optional[int] = None) -> List[AnalysisResult]:
        """Find recent analysis results."""
        async with self._get_session() as session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                query = select(AnalysisResultModel).where(
                    AnalysisResultModel.created_at >= cutoff_date
                ).order_by(desc(AnalysisResultModel.created_at))
                
                if limit:
                    query = query.limit(limit)
                
                result = await session.execute(query)
                analysis_models = result.scalars().all()
                
                return [self._analysis_model_to_entity(model) for model in analysis_models]
                
            except Exception as e:
                self.logger.error(f"Failed to find recent analysis: {str(e)}")
                raise
    
    # Vector operations
    async def save_vector(self, vector_doc: VectorDocument) -> VectorDocument:
        """Save a vector document."""
        async with self._get_session() as session:
            try:
                # Convert domain entity to database model
                vector_model = VectorEmbeddingModel(
                    source_type=vector_doc.source_type.value,
                    source_id=vector_doc.source_id,
                    content_hash=vector_doc.content_hash,
                    embedding=vector_doc.embedding,
                    embedding_model=vector_doc.embedding_model,
                    dimension=vector_doc.dimension,
                    vector_metadata=vector_doc.metadata
                )
                
                session.add(vector_model)
                await session.commit()
                await session.refresh(vector_model)
                
                # Convert back to domain entity
                return self._vector_model_to_entity(vector_model)
                
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to save vector document: {str(e)}")
                raise
    
    async def search_vectors(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """Perform vector similarity search."""
        async with self._get_session() as session:
            try:
                # Build the similarity search query using pgvector
                # Using cosine distance (1 - cosine similarity)
                query_vector_str = f"[{','.join(map(str, query_vector))}]"
                
                base_query = f"""
                SELECT *, (embedding <=> '{query_vector_str}') as distance
                FROM vector_embeddings
                """
                
                where_clause = ""
                if source_type:
                    where_clause = f"WHERE source_type = '{source_type}'"
                
                order_clause = f"ORDER BY distance LIMIT {top_k}"
                
                full_query = f"{base_query} {where_clause} {order_clause}"
                
                result = await session.execute(text(full_query))
                rows = result.fetchall()
                
                search_results = []
                for row in rows:
                    # Convert row to vector model
                    vector_model = VectorEmbeddingModel(
                        id=row.id,
                        source_type=row.source_type,
                        source_id=row.source_id,
                        content_hash=row.content_hash,
                        embedding=row.embedding,
                        embedding_model=row.embedding_model,
                        dimension=row.dimension,
                        vector_metadata=row.vector_metadata,
                        created_at=row.created_at
                    )
                    
                    # Convert to domain entity
                    vector_entity = self._vector_model_to_entity(vector_model)
                    
                    # Calculate similarity score from distance
                    distance = float(row.distance)
                    similarity_score = 1.0 - distance  # Convert distance to similarity
                    
                    search_results.append(VectorSearchResult(
                        document=vector_entity,
                        similarity_score=similarity_score,
                        distance=distance
                    ))
                
                return search_results
                
            except Exception as e:
                self.logger.error(f"Failed to search vectors: {str(e)}")
                raise
    
    async def get_vector_count(self) -> int:
        """Get total number of vectors stored."""
        async with self._get_session() as session:
            try:
                from sqlalchemy import func
                query = select(func.count(VectorEmbeddingModel.id))
                result = await session.execute(query)
                return result.scalar()
                
            except Exception as e:
                self.logger.error(f"Failed to get vector count: {str(e)}")
                raise
    
    # Health check
    async def health_check(self) -> bool:
        """Check if the repository is healthy."""
        try:
            async with self._get_session() as session:
                # Simple query to test database connection
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    # Helper methods for model conversion
    def _news_model_to_entity(self, model: NewsArticleModel) -> NewsArticle:
        """Convert database model to domain entity."""
        return NewsArticle(
            url=model.url,
            title=model.title,
            content=model.content,
            content_hash=model.content_hash,
            source=model.source,
            author=model.author,
            published_at=model.published_at,
            fetched_at=model.fetched_at,
            metadata=model.article_metadata or {},
            processing_status=ProcessingStatus(model.processing_status),
            processing_attempts=model.processing_attempts,
            last_processed_at=model.last_processed_at,
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _analysis_model_to_entity(self, model: AnalysisResultModel) -> AnalysisResult:
        """Convert database model to domain entity."""
        return AnalysisResult(
            article_id=model.article_id,
            analysis_type=AnalysisType(model.analysis_type),
            model_name=model.model_name,
            result=model.result,
            model_version=model.model_version,
            confidence_score=model.confidence_score,
            processing_time_ms=model.processing_time_ms,
            tokens_used=model.tokens_used,
            id=model.id,
            created_at=model.created_at
        )
    
    def _vector_model_to_entity(self, model: VectorEmbeddingModel) -> VectorDocument:
        """Convert database model to domain entity."""
        return VectorDocument(
            source_type=VectorSourceType(model.source_type),
            source_id=model.source_id,
            content_hash=model.content_hash,
            embedding=model.embedding,
            embedding_model=model.embedding_model,
            metadata=model.vector_metadata or {},
            dimension=model.dimension,
            id=model.id,
            created_at=model.created_at
        )