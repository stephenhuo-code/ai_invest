"""
Database Storage Tool for AI Invest platform.

Provides database operations using the unified repository pattern.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_tool import BaseTool, ToolResult, ToolStatus
from ...domain.entities.news_article import NewsArticle, ProcessingStatus
from ...domain.entities.analysis_result import AnalysisResult, AnalysisType
from ...infrastructure.database.unified_repository import UnifiedDatabaseRepository


class DatabaseStorage(BaseTool):
    """Real database storage tool using unified repository."""
    
    def __init__(self, repository: Optional[UnifiedDatabaseRepository] = None):
        super().__init__(
            name="database_storage", 
            description="Store and retrieve data from PostgreSQL database"
        )
        self.repository = repository or UnifiedDatabaseRepository()
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute database operations."""
        try:
            operation = kwargs.get("operation", "health_check")
            
            if operation == "health_check":
                return await self._health_check()
            elif operation == "save_news":
                return await self._save_news(**kwargs)
            elif operation == "save_news_batch":
                return await self._save_news_batch(**kwargs)
            elif operation == "find_recent_news":
                return await self._find_recent_news(**kwargs)
            elif operation == "find_news_by_id":
                return await self._find_news_by_id(**kwargs)
            elif operation == "save_analysis":
                return await self._save_analysis(**kwargs)
            elif operation == "find_analysis_by_news_id":
                return await self._find_analysis_by_news_id(**kwargs)
            elif operation == "find_recent_analysis":
                return await self._find_recent_analysis(**kwargs)
            elif operation == "get_statistics":
                return await self._get_statistics()
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Unknown database operation: {operation}"
                )
                
        except Exception as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Database operation failed: {str(e)}"
            )
    
    async def _health_check(self) -> ToolResult:
        """Check database health."""
        try:
            is_healthy = await self.repository.health_check()
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "healthy": is_healthy,
                    "connection": "active" if is_healthy else "failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Health check failed: {str(e)}"
            )
    
    async def _save_news(self, **kwargs) -> ToolResult:
        """Save a single news article."""
        try:
            news_data = kwargs.get("news_data")
            if not news_data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing news_data parameter"
                )
            
            # Convert dict to NewsArticle entity if needed
            if isinstance(news_data, dict):
                news_article = self._dict_to_news_article(news_data)
            else:
                news_article = news_data
            
            saved_article = await self.repository.save_news(news_article)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "article_id": saved_article.id,
                    "url": saved_article.url,
                    "title": saved_article.title,
                    "source": saved_article.source,
                    "content_hash": saved_article.content_hash,
                    "saved": True,
                    "created_at": saved_article.created_at.isoformat() if saved_article.created_at else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save news article: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to save news article: {str(e)}"
            )
    
    async def _save_news_batch(self, **kwargs) -> ToolResult:
        """Save multiple news articles."""
        try:
            articles_data = kwargs.get("articles_data", [])
            if not articles_data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing articles_data parameter"
                )
            
            saved_articles = []
            errors = []
            
            # Process articles concurrently with a semaphore to limit concurrency
            semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent saves
            
            async def save_single_article(article_data):
                async with semaphore:
                    try:
                        if isinstance(article_data, dict):
                            news_article = self._dict_to_news_article(article_data)
                        else:
                            news_article = article_data
                        
                        saved_article = await self.repository.save_news(news_article)
                        return {
                            "success": True,
                            "article_id": saved_article.id,
                            "title": saved_article.title,
                            "url": saved_article.url
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": str(e),
                            "url": article_data.get("url", "unknown") if isinstance(article_data, dict) else "unknown"
                        }
            
            # Execute all saves concurrently
            results = await asyncio.gather(
                *[save_single_article(article) for article in articles_data],
                return_exceptions=True
            )
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    errors.append(f"Unexpected error: {str(result)}")
                elif result["success"]:
                    saved_articles.append(result)
                else:
                    errors.append(f"Failed to save {result['url']}: {result['error']}")
            
            return ToolResult(
                status=ToolStatus.SUCCESS if saved_articles else ToolStatus.ERROR,
                data={
                    "total_processed": len(articles_data),
                    "successfully_saved": len(saved_articles),
                    "errors": len(errors),
                    "saved_articles": saved_articles,
                    "error_details": errors
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save news batch: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to save news batch: {str(e)}"
            )
    
    async def _find_recent_news(self, **kwargs) -> ToolResult:
        """Find recent news articles."""
        try:
            days = kwargs.get("days", 7)
            limit = kwargs.get("limit", 50)
            include_content = kwargs.get("include_content", False)
            
            articles = await self.repository.find_recent_news(days=days, limit=limit)
            
            # Convert to serializable format
            articles_data = []
            for article in articles:
                article_dict = {
                    "id": article.id,
                    "url": article.url,
                    "title": article.title,
                    "source": article.source,
                    "author": article.author,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "fetched_at": article.fetched_at.isoformat() if article.fetched_at else None,
                    "processing_status": article.processing_status.value,
                    "content_hash": article.content_hash,
                    "created_at": article.created_at.isoformat() if article.created_at else None
                }
                
                # Include full content if requested
                if include_content and hasattr(article, 'content') and article.content:
                    article_dict["content"] = article.content
                
                articles_data.append(article_dict)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "articles": articles_data,
                    "count": len(articles_data),
                    "days_searched": days,
                    "limit_applied": limit,
                    "include_content": include_content
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to find recent news: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to find recent news: {str(e)}"
            )
    
    async def _find_news_by_id(self, **kwargs) -> ToolResult:
        """Find news article by ID."""
        try:
            news_id = kwargs.get("news_id")
            if not news_id:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing news_id parameter"
                )
            
            article = await self.repository.find_news_by_id(news_id)
            
            if not article:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={"found": False, "news_id": news_id}
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "found": True,
                    "article": {
                        "id": article.id,
                        "url": article.url,
                        "title": article.title,
                        "content": article.content,
                        "source": article.source,
                        "author": article.author,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "processing_status": article.processing_status.value,
                        "created_at": article.created_at.isoformat() if article.created_at else None
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to find news by ID: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to find news by ID: {str(e)}"
            )
    
    async def _save_analysis(self, **kwargs) -> ToolResult:
        """Save an analysis result."""
        try:
            analysis_data = kwargs.get("analysis_data")
            if not analysis_data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing analysis_data parameter"
                )
            
            # Convert dict to AnalysisResult entity if needed
            if isinstance(analysis_data, dict):
                analysis_result = self._dict_to_analysis_result(analysis_data)
            else:
                analysis_result = analysis_data
            
            saved_analysis = await self.repository.save_analysis(analysis_result)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "analysis_id": saved_analysis.id,
                    "article_id": saved_analysis.article_id,
                    "analysis_type": saved_analysis.analysis_type.value,
                    "model_name": saved_analysis.model_name,
                    "confidence_score": saved_analysis.confidence_score,
                    "saved": True,
                    "created_at": saved_analysis.created_at.isoformat() if saved_analysis.created_at else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to save analysis: {str(e)}"
            )
    
    async def _find_analysis_by_news_id(self, **kwargs) -> ToolResult:
        """Find analysis results for a news article."""
        try:
            news_id = kwargs.get("news_id")
            if not news_id:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message="Missing news_id parameter"
                )
            
            analyses = await self.repository.find_analysis_by_news_id(news_id)
            
            # Convert to serializable format
            analyses_data = []
            for analysis in analyses:
                analyses_data.append({
                    "id": analysis.id,
                    "article_id": analysis.article_id,
                    "analysis_type": analysis.analysis_type.value,
                    "model_name": analysis.model_name,
                    "result": analysis.result,
                    "confidence_score": analysis.confidence_score,
                    "processing_time_ms": analysis.processing_time_ms,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "analyses": analyses_data,
                    "count": len(analyses_data),
                    "news_id": news_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to find analysis by news ID: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to find analysis by news ID: {str(e)}"
            )
    
    async def _find_recent_analysis(self, **kwargs) -> ToolResult:
        """Find recent analysis results."""
        try:
            days = kwargs.get("days", 7)
            limit = kwargs.get("limit", 50)
            
            analyses = await self.repository.find_recent_analysis(days=days, limit=limit)
            
            # Convert to serializable format
            analyses_data = []
            for analysis in analyses:
                analyses_data.append({
                    "id": analysis.id,
                    "article_id": analysis.article_id,
                    "analysis_type": analysis.analysis_type.value,
                    "model_name": analysis.model_name,
                    "confidence_score": analysis.confidence_score,
                    "result": analysis.result,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "analyses": analyses_data,
                    "count": len(analyses_data),
                    "days_searched": days,
                    "limit_applied": limit
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to find recent analysis: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to find recent analysis: {str(e)}"
            )
    
    async def _get_statistics(self) -> ToolResult:
        """Get database statistics."""
        try:
            # Get vector count from repository
            vector_count = await self.repository.get_vector_count()
            
            # Get recent news and analysis counts
            recent_news = await self.repository.find_recent_news(days=7, limit=1000)  # Large limit to get count
            recent_analysis = await self.repository.find_recent_analysis(days=7, limit=1000)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "vector_count": vector_count,
                    "recent_news_count": len(recent_news),
                    "recent_analysis_count": len(recent_analysis),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Failed to get statistics: {str(e)}"
            )
    
    def _dict_to_news_article(self, data: Dict[str, Any]) -> NewsArticle:
        """Convert dictionary to NewsArticle entity."""
        return NewsArticle(
            url=data.get("url", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            content_hash=data.get("content_hash", ""),
            source=data.get("source", ""),
            author=data.get("author"),
            published_at=data.get("published_at"),
            fetched_at=data.get("fetched_at", datetime.utcnow()),
            metadata=data.get("metadata", {}),
            processing_status=ProcessingStatus.PENDING
        )
    
    def _dict_to_analysis_result(self, data: Dict[str, Any]) -> AnalysisResult:
        """Convert dictionary to AnalysisResult entity."""
        return AnalysisResult(
            article_id=data.get("article_id"),
            analysis_type=AnalysisType(data.get("analysis_type", "sentiment")),
            model_name=data.get("model_name", "gpt-4o"),
            result=data.get("result", {}),
            model_version=data.get("model_version"),
            confidence_score=data.get("confidence_score", 0.0),
            processing_time_ms=data.get("processing_time_ms", 0),
            tokens_used=data.get("tokens_used", 0)
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        return {
            "parameters": {
                "operation": {
                    "type": "string", 
                    "enum": [
                        "health_check", "save_news", "save_news_batch", "find_recent_news", 
                        "find_news_by_id", "save_analysis", "find_analysis_by_news_id", 
                        "find_recent_analysis", "get_statistics"
                    ],
                    "description": "Database operation to perform"
                },
                "news_data": {
                    "type": "object", 
                    "description": "News article data for save_news operation"
                },
                "articles_data": {
                    "type": "array", 
                    "description": "Array of news articles for save_news_batch operation"
                },
                "analysis_data": {
                    "type": "object", 
                    "description": "Analysis result data for save_analysis operation"
                },
                "news_id": {
                    "type": "integer", 
                    "description": "News article ID for lookup operations"
                },
                "days": {
                    "type": "integer", 
                    "description": "Number of days to look back for recent data",
                    "default": 7
                },
                "limit": {
                    "type": "integer", 
                    "description": "Maximum number of results to return",
                    "default": 50
                }
            },
            "required": ["operation"]
        }