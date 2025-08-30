"""
Database connection management.

Handles PostgreSQL connections using SQLAlchemy with async support.
Includes repository factory for the new unified architecture.
"""
import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

# Create base class for SQLAlchemy models
Base = declarative_base()

# Global database manager instance
_db_manager: Optional["DatabaseManager"] = None
# Global repository instance
_repository: Optional["UnifiedDatabaseRepository"] = None

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for handling PostgreSQL connections with async support.
    
    Supports both development (local PostgreSQL) and production (Azure PostgreSQL) environments.
    """
    
    def __init__(self):
        self._async_engine: Optional[AsyncEngine] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._database_url: Optional[str] = None
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None) -> None:
        """
        Initialize the database manager.
        
        Args:
            database_url: Optional database URL override
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return
        
        # Get database URL from environment or parameter
        self._database_url = database_url or self._build_database_url()
        
        # Create async engine
        self._async_engine = create_async_engine(
            self._database_url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,   # Recycle connections every hour
            # Use NullPool for async to avoid connection issues
            poolclass=NullPool if os.getenv("ENVIRONMENT") == "production" else None,
        )
        
        # Create async session factory
        self._async_session_factory = async_sessionmaker(
            bind=self._async_engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
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
    
    @property
    def async_engine(self) -> AsyncEngine:
        """Get the async engine."""
        if not self._initialized or self._async_engine is None:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        return self._async_engine
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session as a context manager.
        
        Usage:
            async with db_manager.get_async_session() as session:
                # Use session here
                result = await session.execute(query)
                await session.commit()
        """
        if not self._initialized or self._async_session_factory is None:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._initialized or self._async_engine is None:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        # Import models to ensure they're registered with Base
        from . import models  # noqa: F401
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        if not self._initialized or self._async_engine is None:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        # Import models to ensure they're registered with Base
        from . import models  # noqa: F401
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped successfully")
    
    async def health_check(self) -> bool:
        """
        Check database health.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            async with self.get_async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the database connection."""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Database connections closed")


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        The database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """
    Initialize the database manager and create tables.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        The initialized database manager
    """
    db_manager = get_db_manager()
    db_manager.initialize(database_url)
    
    # Create tables if they don't exist
    await db_manager.create_tables()
    
    return db_manager


def get_repository():
    """
    Get the global unified repository instance.
    
    Returns:
        The unified database repository instance
    """
    global _repository
    if _repository is None:
        from .unified_repository import UnifiedDatabaseRepository
        _repository = UnifiedDatabaseRepository()
    return _repository


def create_agents(repository=None):
    """
    Create and configure agents with the unified repository.
    
    Args:
        repository: Optional repository instance (uses global if not provided)
        
    Returns:
        Tuple of (DataAgent, AnalysisAgent)
    """
    if repository is None:
        repository = get_repository()
    
    from ...application.agents import DataAgent, AnalysisAgent
    
    data_agent = DataAgent(repository)
    analysis_agent = AnalysisAgent(repository)
    
    return data_agent, analysis_agent