"""
LLM-powered Data Agent for AI Invest platform.

A simplified intelligent agent that handles data acquisition, processing, and storage operations
using natural language understanding and reasoning capabilities.
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .llm_base_agent import BaseLLMAgent, LLMAgentTask, LLMAgentResult, LLMTaskType
from ..tools.rss_news_fetcher import RSSNewsFetcher
from ..tools.market_data import MarketDataFetcher
from ...infrastructure.database.simple_pg_db import get_simple_db, ensure_tables










class LLMDataAgent(BaseLLMAgent):
    """
    LLM-powered Data Agent for intelligent data operations.
    
    This agent can understand natural language requests and intelligently:
    - Fetch financial news from various RSS sources  
    - Collect market data from APIs
    - Process and clean data using advanced techniques
    - Store data in databases and vector storage systems
    - Assess data quality and provide recommendations
    - Handle complex data workflows with multi-step reasoning
    
    Examples of tasks it can handle:
    - "Get the latest tech stock news from the past 24 hours and store in database"
    - "Fetch Apple stock data for the last month and analyze price trends"
    - "Find news articles about renewable energy companies and create embeddings"
    - "Check data quality of recent news articles and fix any issues"
    """
    
    def __init__(
        self, 
        llm: Optional[ChatOpenAI] = None,
        enable_market_data: bool = True,
        max_articles_per_source: int = 50
    ):
        # Initialize simplified database access
        self.db = get_simple_db()
        
        # Initialize real tools (simplified)
        tools = [RSSNewsFetcher()]
        
        # Add market data tool if enabled
        if enable_market_data:
            tools.append(MarketDataFetcher())
        
        super().__init__(
            name="DataAgent",
            description="I am an intelligent data specialist focused on financial news and market data acquisition, processing, and storage using real RSS feeds and simplified PostgreSQL database access",
            tools=tools,
            llm=llm,
            memory_window=15,
            max_iterations=20
        )
        
        self.max_articles_per_source = max_articles_per_source
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the DataAgent's specialized prompt."""
        return ChatPromptTemplate.from_template("""You are DataAgent, an expert AI assistant specialized in financial data acquisition and processing.

Your core capabilities include:
- Fetching financial news from real RSS feeds (Yahoo Finance, CNBC, Reuters, etc.)
- Collecting live stock market data using yfinance API
- Processing and cleaning textual and numerical data
- Storing data in PostgreSQL database with proper schemas
- Creating OpenAI embeddings and storing them in pgvector
- Performing vector similarity searches
- Assessing data quality and providing validation reports
- Handling multi-source data aggregation with deduplication
- Managing complete data workflows with comprehensive error handling

You have access to these tools: {tools}
Tool names: {tool_names}

When given a task:
1. Analyze the request to understand what data operations are needed
2. Plan the sequence of tool usage to accomplish the goal
3. Execute the plan step by step, adapting based on results
4. Provide clear feedback about what was accomplished
5. Handle errors gracefully and suggest alternatives if needed

Always be thorough, accurate, and explain your reasoning process.

User input: {input}
Agent scratchpad: {agent_scratchpad}""")
    
    def get_capabilities(self) -> List[str]:
        """Get list of DataAgent capabilities."""
        return [
            "fetch_news: Fetch financial news from RSS feeds and web sources",
            "fetch_market_data: Collect stock market data from Yahoo Finance and other APIs", 
            "process_data: Process and clean textual and numerical data",
            "store_data: Store data in PostgreSQL database with proper schemas",
            "create_embeddings: Create and store vector embeddings in pgvector",
            "assess_quality: Assess data quality and provide validation reports",
            "aggregate_data: Handle multi-source data aggregation with deduplication",
            "manage_workflows: Perform intelligent data workflows with error handling",
            "monitor_sources: Monitor data sources for updates and changes",
            "optimize_storage: Optimize data storage and retrieval performance"
        ]
    
    # Convenience methods for common operations
    
    async def fetch_news(
        self, 
        sources: Optional[List[str]] = None,
        max_articles: int = 10,
        store_results: bool = True
    ) -> LLMAgentResult:
        """Fetch news using simplified direct database access."""
        start_time = datetime.utcnow()
        task_id = f"fetch_news_{hash(str(sources))%10000}"
        
        try:
            # Ensure database tables exist
            await ensure_tables()
            
            # Use default sources if none specified
            if not sources:
                from ...config.rss_sources import get_reliable_rss_sources
                sources = get_reliable_rss_sources()
            
            self.logger.info(f"Starting news fetch: {len(sources)} sources, max {max_articles} articles, store={store_results}")
            
            # Step 1: Fetch news using RSS tool
            rss_tool = None
            for tool in self.tools:
                if 'rss' in tool.name.lower() or 'news' in tool.name.lower():
                    rss_tool = tool
                    break
            
            if not rss_tool:
                return LLMAgentResult(
                    task_id=task_id,
                    success=False,
                    error_message="RSS news fetcher tool not found",
                    execution_time_ms=0,
                    tools_used=[]
                )
            
            # Execute RSS fetch
            rss_result = await rss_tool.execute(
                rss_urls=sources,
                max_articles=max_articles,
                hours_back=24,
                include_content=True
            )
            
            if not rss_result.is_success:
                return LLMAgentResult(
                    task_id=task_id,
                    success=False,
                    error_message=f"RSS fetch failed: {rss_result.error_message}",
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    tools_used=['rss_news_fetcher']
                )
            
            articles_data = rss_result.data.get('articles', [])
            tools_used = ['rss_news_fetcher']
            
            if not store_results:
                # Return data without storage
                return LLMAgentResult(
                    task_id=task_id,
                    success=True,
                    result={
                        'articles': articles_data,
                        'total_fetched': len(articles_data),
                        'sources_used': sources
                    },
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    tools_used=tools_used
                )
            
            # Step 2: Store articles using simplified database access
            stored_articles = []
            if articles_data:
                try:
                    stored_articles = await self.db.save_news_batch(articles_data)
                    tools_used.append('simple_pg_db')
                    self.logger.info(f"Stored {len(stored_articles)} articles using SimplePGDB")
                except Exception as e:
                    self.logger.warning(f"SimplePGDB storage failed: {str(e)}")
            
            # Note: Vector embeddings removed for simplification
            # Can be added back later if needed
            
            # Return comprehensive result
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return LLMAgentResult(
                task_id=task_id,
                success=True,
                result={
                    'articles_fetched': len(articles_data),
                    'articles_stored': len(stored_articles),
                    'vectors_created': 0,  # Simplified - no vectors for now
                    'sources_used': sources,
                    'articles': articles_data[:5],  # Return first 5 for inspection
                    'storage_summary': {
                        'database_success': len(stored_articles) > 0,
                        'vector_success': False  # Simplified
                    }
                },
                execution_time_ms=execution_time,
                tools_used=tools_used
            )
            
        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            self.logger.error(f"fetch_news failed: {str(e)}")
            
            return LLMAgentResult(
                task_id=task_id,
                success=False,
                error_message=f"fetch_news execution failed: {str(e)}",
                execution_time_ms=execution_time,
                tools_used=[]
            )
    
    async def get_market_data(
        self, 
        symbols: List[str],
        timeframe: str = "1d"
    ) -> LLMAgentResult:
        """Convenience method to get market data using natural language."""
        task = LLMAgentTask(
            task_id=f"market_data_{hash(','.join(symbols))%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Use the market_data tool to get live market data for stocks {', '.join(symbols)} with {timeframe} timeframe including current prices, changes, volumes, and key financial metrics",
            parameters={
                "symbols": symbols,
                "timeframe": timeframe
            }
        )
        return await self.execute_task(task)
    
    async def health_check(self) -> Dict[str, Any]:
        """Convenience method for health checking data systems."""
        task = LLMAgentTask(
            task_id=f"health_{hash(str(asyncio.get_event_loop().time()))%10000}",
            task_type=LLMTaskType.STRUCTURED,
            description="Use database_storage and vector_storage tools to perform comprehensive health checks on all data systems including database connectivity, vector storage status, and system statistics",
            parameters={"check_all_systems": True}
        )
        result = await self.execute_task(task)
        
        if result.success and isinstance(result.result, dict):
            return result.result
        else:
            return {
                "overall_healthy": False,
                "error": result.error_message or "Health check failed", 
                "details": {}
            }