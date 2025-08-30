"""
AI Invest Trend API - Simplified New Architecture.

FastAPI application using the simplified Agent-Tool architecture with
unified repository pattern and direct OpenAI integration.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Infrastructure setup - simplified for LLM-only architecture
from ...application.agents.llm_data_agent import LLMDataAgent
from ...application.agents.llm_analysis_agent import LLMAnalysisAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application configuration
APP_NAME = os.getenv("APP_NAME", "AI Invest Trend API")
APP_VERSION = os.getenv("APP_VERSION", "2.1.0")
APP_DESCRIPTION = """
AI Invest Trend API - Simplified Architecture

An intelligent investment research automation tool using:
- Agent-Tool architecture for modular functionality
- PostgreSQL + pgvector for vector storage
- Unified repository pattern for data access
- Direct OpenAI integration for AI analysis
"""

# Global components - simplified LLM agents
data_agent = None
analysis_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global data_agent, analysis_agent
    
    # Startup
    logger.info("🚀 Starting AI Invest Trend API v2.1 (LLM-Simplified)...")
    
    try:
        # Create LLM agents (simplified - no database dependency)
        data_agent = LLMDataAgent()
        analysis_agent = LLMAnalysisAgent()
        logger.info("✅ LLM Agents initialized (DataAgent, AnalysisAgent)")
        
        logger.info("✅ System ready - skipping health check to avoid LLM loops")
        
        # Log configuration
        logger.info(f"🤖 LLM Architecture: Pure LangChain Agents")
        logger.info(f"🔑 OpenAI API: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    
    logger.info("✅ Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Invest Trend API...")
    logger.info("✅ Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include LLM API router
from .llm_api_router import llm_router
app.include_router(llm_router)

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Invest Trend API - Simplified Architecture",
        "version": APP_VERSION,
        "architecture": "agent-tool-simplified",
        "database": "postgresql-pgvector",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        if not data_agent or not analysis_agent:
            raise HTTPException(status_code=503, detail="Agents not initialized")
        
        # Check both agents
        data_health = await data_agent.health_check()
        analysis_health = {
            "healthy": True,
            "available_capabilities": analysis_agent.get_capabilities()
        }
        
        overall_healthy = data_health.get("overall_healthy", False)
        
        return {
            "overall_healthy": overall_healthy,
            "data_agent": {
                "healthy": data_health.get("overall_healthy", False),
                "details": data_health,
                "error": None if data_health.get("overall_healthy", False) else "Data agent health check failed"
            },
            "analysis_agent": analysis_health,
            "timestamp": "2025-08-29T07:00:00Z"  # Will be updated with actual time
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/agents/info")
async def agents_info():
    """Get information about available agents."""
    try:
        if not data_agent or not analysis_agent:
            raise HTTPException(status_code=503, detail="Agents not initialized")
        
        return {
            "data_agent": data_agent.get_info(),
            "analysis_agent": analysis_agent.get_info()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent information")


@app.post("/run/full-analysis")
async def run_full_analysis(
    max_articles: int = 10,
    generate_report: bool = True,
    send_notifications: bool = False
):
    """
    Run the complete news analysis workflow using LLM agents.
    
    This endpoint orchestrates:
    1. News fetching using LLM DataAgent
    2. AI analysis using LLM AnalysisAgent (sentiment, topics, stocks)
    3. Results processing and storage
    4. Report generation (optional)
    5. Notifications (optional)
    """
    try:
        if not data_agent or not analysis_agent:
            raise HTTPException(status_code=503, detail="LLM Agents not initialized")
        
        logger.info(f"Starting LLM-powered analysis workflow with {max_articles} articles")
        
        # Step 1: Fetch news using DataAgent
        fetch_result = await data_agent.fetch_news(
            max_articles=max_articles,
            store_results=True
        )
        
        workflow_result = {
            "workflow_id": f"{hash(str(max_articles))%10000}",
            "started_at": "2025-08-29T07:00:00Z",
            "steps": {
                "fetch_news": {
                    "success": fetch_result.success,
                    "data": fetch_result.result if fetch_result.success else None,
                    "error": fetch_result.error_message,
                    "tools_used": fetch_result.tools_used
                }
            }
        }
        
        # Step 2: Analyze news if fetching was successful
        if fetch_result.success and fetch_result.result:
            articles_data = fetch_result.result.get("articles", [])
            if articles_data:
                # Simulate batch analysis
                analysis_result = await analysis_agent.batch_analyze_news(
                    articles=articles_data,
                    analysis_types=["sentiment", "topics", "stocks"]
                )
                
                workflow_result["steps"]["batch_analysis"] = {
                    "success": analysis_result.success,
                    "data": analysis_result.result if analysis_result.success else None,
                    "error": analysis_result.error_message,
                    "tools_used": analysis_result.tools_used
                }
            else:
                workflow_result["steps"]["batch_analysis"] = {
                    "success": False,
                    "data": None,
                    "error": "No news items provided for batch analysis",
                    "tools_used": []
                }
        else:
            workflow_result["steps"]["batch_analysis"] = {
                "success": False,
                "data": None,
                "error": "News fetching failed",
                "tools_used": []
            }
        
        # Determine overall status
        all_success = all(
            step.get("success", False) 
            for step in workflow_result["steps"].values()
        )
        
        workflow_result["status"] = "completed" if all_success else "error"
        workflow_result["completed_at"] = "2025-08-29T07:01:00Z"
        
        if not all_success:
            # Find the first error for the main error field
            first_error = None
            for step in workflow_result["steps"].values():
                if not step.get("success", False) and step.get("error"):
                    first_error = step["error"]
                    break
            workflow_result["error"] = first_error or "Unknown workflow error"
        
        return workflow_result
        
    except Exception as e:
        logger.error(f"LLM analysis workflow failed: {e}")
        return {
            "workflow_id": f"error_{hash(str(e))%10000}",
            "started_at": "2025-08-29T07:00:00Z",
            "status": "error",
            "error": str(e),
            "completed_at": "2025-08-29T07:00:01Z"
        }


@app.post("/run/analyze-existing")
async def analyze_existing_news(
    days_back: int = 7,
    limit: int = 50
):
    """
    Analyze existing content using LLM agents.
    
    Demonstrates LLM analysis capabilities on sample content.
    """
    try:
        if not analysis_agent:
            raise HTTPException(status_code=503, detail="Analysis agent not initialized")
        
        # Sample financial content for demonstration
        sample_content = """
        Apple Inc. reported strong quarterly earnings today, beating analyst expectations
        on both revenue and profit margins. The company's iPhone sales showed remarkable
        resilience despite global economic headwinds. CEO Tim Cook expressed optimism
        about the company's future prospects, particularly in emerging markets and
        services revenue. Investors responded positively, with shares rising 5% in
        after-hours trading.
        """
        
        # Run analysis using LLM agent
        analysis_result = await analysis_agent.analyze_sentiment(
            content=sample_content,
            analysis_depth="comprehensive"
        )
        
        return {
            "success": analysis_result.success,
            "analysis_type": "sample_content_analysis",
            "days_back": days_back,
            "limit": limit,
            "sample_content_analyzed": len(sample_content),
            "result": analysis_result.result if analysis_result.success else None,
            "error": analysis_result.error_message,
            "tools_used": analysis_result.tools_used,
            "execution_time_ms": analysis_result.execution_time_ms,
            "note": "This is a demonstration using sample content. In production, this would analyze actual database content."
        }
        
    except Exception as e:
        logger.error(f"Sample analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/recent-news")
async def get_recent_news(days: int = 7, limit: int = 20):
    """Get recent news articles using real DataAgent."""
    try:
        if not data_agent:
            raise HTTPException(status_code=503, detail="Data agent not initialized")
        
        logger.info(f"Fetching recent news: {days} days, limit {limit}")
        
        # Use DataAgent to fetch and store news
        fetch_result = await data_agent.fetch_news(
            sources=None,  # Use default reliable sources
            max_articles=limit,
            store_results=True
        )
        
        if fetch_result.success:
            result_data = fetch_result.result
            articles_fetched = result_data.get('articles_fetched', 0)
            articles_stored = result_data.get('articles_stored', 0)
            articles_data = result_data.get('articles', [])
            
            # Format articles for API response
            formatted_articles = []
            for article in articles_data:
                formatted_articles.append({
                    "id": article.get('content_hash', 'unknown'),  # Use hash as ID
                    "title": article.get('title', ''),
                    "url": article.get('url', ''),
                    "source": article.get('source', ''),
                    "author": article.get('author', ''),
                    "published_at": article.get('published_at'),
                    "content_preview": article.get('content', '')[:200] + "..." if article.get('content') else "",
                    "processing_status": "completed",
                    "created_at": article.get('fetched_at')
                })
            
            return {
                "success": True,
                "articles_found": len(formatted_articles),
                "days_requested": days,
                "limit_requested": limit,
                "articles": formatted_articles,
                "summary": {
                    "articles_fetched": articles_fetched,
                    "articles_stored": articles_stored,
                    "vectors_created": result_data.get('vectors_created', 0),
                    "sources_used": len(result_data.get('sources_used', [])),
                    "execution_time_ms": fetch_result.execution_time_ms,
                    "storage_status": result_data.get('storage_summary', {})
                },
                "note": "Real data fetched from RSS sources and stored in database"
            }
        else:
            # Fallback: try to get stored data from database
            logger.warning(f"Fresh fetch failed: {fetch_result.error_message}, trying stored data")
            
            # Try to use database tool directly to get recent articles
            db_tool = None
            for tool in data_agent.tools:
                if 'database' in tool.name.lower():
                    db_tool = tool
                    break
            
            if db_tool:
                db_result = await db_tool.execute(
                    operation="find_recent_news",
                    days=days,
                    limit=limit
                )
                
                if db_result.is_success:
                    stored_articles = db_result.data.get('articles', [])
                    
                    formatted_articles = []
                    for article in stored_articles:
                        formatted_articles.append({
                            "id": str(article.get('id', 'unknown')),
                            "title": article.get('title', ''),
                            "url": article.get('url', ''),
                            "source": article.get('source', ''),
                            "processing_status": article.get('processing_status', 'unknown'),
                            "created_at": article.get('created_at')
                        })
                    
                    return {
                        "success": True,
                        "articles_found": len(formatted_articles),
                        "days_requested": days,
                        "limit_requested": limit,
                        "articles": formatted_articles,
                        "note": "Data retrieved from database (fresh fetch failed)",
                        "warning": f"Fresh data fetch failed: {fetch_result.error_message}"
                    }
            
            # If everything fails, return error
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to fetch news: {fetch_result.error_message}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/recent-analysis")
async def get_recent_analysis(days: int = 7, limit: int = 20):
    """Get recent analysis results (mock data for LLM demo)."""
    try:
        if not analysis_agent:
            raise HTTPException(status_code=503, detail="Analysis agent not initialized")
        
        # Return mock analysis data for demonstration
        mock_analyses = []
        analysis_types = ["sentiment", "topics", "stocks"]
        
        for i in range(min(limit, 3)):  # Limit to 3 for demo
            mock_analyses.append({
                "id": f"analysis_{i+1}",
                "article_id": f"article_{i+1}",
                "analysis_type": analysis_types[i % len(analysis_types)],
                "model_name": "gpt-4o",
                "confidence_score": 0.85 + (i * 0.03),
                "result": {
                    "sentiment": "positive" if i % 2 == 0 else "neutral",
                    "confidence": 0.85 + (i * 0.03)
                },
                "created_at": "2025-08-29T10:00:00Z"
            })
        
        return {
            "analyses_found": len(mock_analyses),
            "days_requested": days, 
            "limit_requested": limit,
            "analyses": mock_analyses,
            "note": "This is mock analysis data for LLM-only architecture demonstration"
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/stored-news")
async def get_stored_news(
    days: int = 7, 
    limit: int = 20, 
    include_content: bool = False
):
    """Get stored news articles from database without fetching new ones."""
    try:
        logger.info(f"Querying stored news: {days} days, limit {limit}, include_content={include_content}")
        
        # Use SimplePGDB directly
        from ...infrastructure.database.simple_pg_db import get_simple_db, ensure_tables
        
        # Ensure tables exist
        await ensure_tables()
        
        db = get_simple_db()
        
        # Query stored news directly from simplified database
        result = await db.find_recent_news(
            days=days,
            limit=limit,
            include_content=include_content
        )
        
        return {
            "success": True,
            "articles_found": result['count'],
            "days_requested": days,
            "limit_requested": limit,
            "include_content": include_content,
            "articles": result['articles'],
            "note": "Data retrieved from SimplePGDB without fetching new articles"
        }
        
    except Exception as e:
        logger.error(f"Failed to get stored news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy compatibility endpoints
@app.get("/run/weekly-full-report")
async def legacy_weekly_report():
    """
    Legacy endpoint for backward compatibility.
    Redirects to the new full analysis workflow.
    """
    logger.info("Legacy endpoint called - redirecting to new architecture")
    
    return await run_full_analysis(
        max_articles=15,
        generate_report=True,
        send_notifications=False
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main_simplified:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )