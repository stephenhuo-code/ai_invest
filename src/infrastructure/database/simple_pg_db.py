"""
Simplified PostgreSQL database access for AI Invest platform.

Direct database operations without complex abstractions.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, text, desc
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)

# Create base for simplified models
Base = declarative_base()


class NewsArticle(Base):
    """Simplified news article model with core fields only."""
    __tablename__ = 'news_articles'
    
    # Core fields only
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(1024), nullable=False)
    url = Column(String(2048), nullable=False, unique=True, index=True)
    content = Column(Text)  # Full article content
    source = Column(String(256), nullable=False, index=True)
    author = Column(String(512))
    published_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    content_hash = Column(String(64), nullable=False, index=True)
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source}')>"


class SimplePGDB:
    """
    Simplified PostgreSQL database access.
    
    Provides direct database operations without complex abstractions.
    Auto-initializes connection and creates tables on first use.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._engine = None
        self._session_factory = None
        self._initialized = False
        
        # Initialize database connection
        self._init_connection()
    
    def _init_connection(self):
        """Initialize database connection and session factory."""
        try:
            # Get database URL from environment
            database_url = self._build_database_url()
            
            # Create async engine
            self._engine = create_async_engine(
                database_url,
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            self.logger.info("✅ SimplePGDB initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize SimplePGDB: {e}")
            raise
    
    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        # Check for full DATABASE_URL first
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Ensure it uses asyncpg driver
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif not database_url.startswith("postgresql+asyncpg://"):
                database_url = "postgresql+asyncpg://" + database_url
            return database_url
        
        # Build from individual components
        host = os.getenv("DATABASE_HOST", "localhost")
        port = os.getenv("DATABASE_PORT", "5432")
        database = os.getenv("DATABASE_NAME", "ai_invest")
        user = os.getenv("DATABASE_USER", "ai_invest")
        password = os.getenv("DATABASE_PASSWORD", "ai_invest_password")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    async def init_tables(self):
        """Create database tables if they don't exist."""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.logger.info("✅ Database tables created/verified")
        except Exception as e:
            self.logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    async def clear_all_data(self):
        """Clear all data from tables (for testing/reset)."""
        try:
            async with self._session_factory() as session:
                await session.execute(text("TRUNCATE TABLE news_articles RESTART IDENTITY CASCADE"))
                await session.commit()
            self.logger.info("✅ All data cleared from database")
        except Exception as e:
            self.logger.error(f"❌ Failed to clear data: {e}")
            raise
    
    async def save_news_batch(self, articles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Save multiple news articles in batch."""
        if not articles_data:
            return []
        
        try:
            async with self._session_factory() as session:
                saved_articles = []
                
                for article_data in articles_data:
                    # Use ON CONFLICT to handle duplicates
                    stmt = insert(NewsArticle).values(
                        title=article_data.get('title', ''),
                        url=article_data.get('url', ''),
                        content=article_data.get('content', ''),
                        source=article_data.get('source', ''),
                        author=article_data.get('author'),
                        published_at=article_data.get('published_at'),
                        content_hash=article_data.get('content_hash', ''),
                        created_at=datetime.utcnow()
                    )
                    
                    # On conflict, update the existing record
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['url'],
                        set_=dict(
                            title=stmt.excluded.title,
                            content=stmt.excluded.content,
                            author=stmt.excluded.author,
                            published_at=stmt.excluded.published_at
                        )
                    )
                    
                    result = await session.execute(stmt)
                    
                    # Get the saved article
                    article_query = select(NewsArticle).where(NewsArticle.url == article_data.get('url'))
                    saved_article = await session.scalar(article_query)
                    
                    if saved_article:
                        saved_articles.append({
                            'id': saved_article.id,
                            'title': saved_article.title,
                            'url': saved_article.url,
                            'source': saved_article.source
                        })
                
                await session.commit()
                self.logger.info(f"✅ Saved {len(saved_articles)} articles to database")
                return saved_articles
                
        except Exception as e:
            self.logger.error(f"❌ Failed to save news batch: {e}")
            raise
    
    async def find_recent_news(
        self, 
        days: int = 7, 
        limit: int = 20, 
        include_content: bool = False
    ) -> Dict[str, Any]:
        """Find recent news articles."""
        try:
            async with self._session_factory() as session:
                # Build query
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                query = select(NewsArticle).where(
                    NewsArticle.created_at >= cutoff_date
                ).order_by(desc(NewsArticle.created_at)).limit(limit)
                
                result = await session.execute(query)
                articles = result.scalars().all()
                
                # Convert to dict format
                articles_data = []
                for article in articles:
                    article_dict = {
                        'id': article.id,
                        'title': article.title,
                        'url': article.url,
                        'source': article.source,
                        'author': article.author,
                        'published_at': article.published_at.isoformat() if article.published_at else None,
                        'created_at': article.created_at.isoformat() if article.created_at else None,
                        'content_hash': article.content_hash
                    }
                    
                    # Include content if requested
                    if include_content and article.content:
                        article_dict['content'] = article.content
                    
                    articles_data.append(article_dict)
                
                self.logger.info(f"✅ Found {len(articles_data)} articles from last {days} days")
                
                return {
                    'articles': articles_data,
                    'count': len(articles_data),
                    'days_searched': days,
                    'limit_applied': limit,
                    'include_content': include_content
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to find recent news: {e}")
            raise
    
    async def get_article_by_id(self, article_id: int, include_content: bool = True) -> Optional[Dict[str, Any]]:
        """Get a specific article by ID."""
        try:
            async with self._session_factory() as session:
                query = select(NewsArticle).where(NewsArticle.id == article_id)
                result = await session.execute(query)
                article = result.scalar()
                
                if not article:
                    return None
                
                article_dict = {
                    'id': article.id,
                    'title': article.title,
                    'url': article.url,
                    'source': article.source,
                    'author': article.author,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'created_at': article.created_at.isoformat() if article.created_at else None,
                    'content_hash': article.content_hash
                }
                
                if include_content and article.content:
                    article_dict['content'] = article.content
                
                return article_dict
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get article by ID: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            async with self._session_factory() as session:
                # Get total count
                total_count_result = await session.execute(
                    select(text("COUNT(*)")).select_from(NewsArticle)
                )
                total_count = total_count_result.scalar()
                
                # Get latest article
                latest_result = await session.execute(
                    select(NewsArticle.created_at).order_by(desc(NewsArticle.created_at)).limit(1)
                )
                latest_date = latest_result.scalar()
                
                # Get source counts
                source_counts_result = await session.execute(
                    text("SELECT source, COUNT(*) FROM news_articles GROUP BY source")
                )
                source_counts = dict(source_counts_result.fetchall())
                
                return {
                    'total_articles': total_count,
                    'latest_article_date': latest_date.isoformat() if latest_date else None,
                    'sources': source_counts,
                    'total_sources': len(source_counts)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get statistics: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self.logger.info("✅ Database connections closed")


# Global instance (singleton pattern)
_db_instance: Optional[SimplePGDB] = None


def get_simple_db() -> SimplePGDB:
    """Get global SimplePGDB instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SimplePGDB()
    return _db_instance


async def ensure_tables():
    """Ensure database tables exist."""
    db = get_simple_db()
    await db.init_tables()