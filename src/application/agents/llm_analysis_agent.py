"""
LLM-powered Analysis Agent for AI Invest platform.

A simplified intelligent agent that performs sophisticated AI analysis of financial content
using natural language understanding and advanced reasoning capabilities.
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .llm_base_agent import BaseLLMAgent, LLMAgentTask, LLMAgentResult, LLMTaskType
from ..tools.base_tool import BaseTool, ToolResult, ToolStatus
from ..tools.database_storage import DatabaseStorage
from ..tools.vector_storage import VectorStorage
from ...infrastructure.database.unified_repository import UnifiedDatabaseRepository


class MockOpenAIAnalysisTool(BaseTool):
    """Mock OpenAI analysis tool for demo purposes."""
    
    def __init__(self):
        super().__init__("openai_analysis", "Perform AI-powered analysis of financial content")
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute mock AI analysis."""
        content = kwargs.get("content", "")
        analysis_type = kwargs.get("analysis_type", "sentiment")
        
        # Mock analysis results
        if analysis_type == "sentiment":
            result = {
                "sentiment": "positive",
                "confidence": 0.85,
                "reasoning": "The content contains optimistic language about market performance and growth prospects."
            }
        elif analysis_type == "topics":
            result = {
                "topics": ["technology", "market_analysis", "investment"],
                "themes": ["AI development", "stock performance", "financial forecasts"],
                "confidence": 0.78
            }
        elif analysis_type == "stocks":
            result = {
                "stock_mentions": [
                    {"symbol": "AAPL", "company": "Apple Inc.", "context": "positive"},
                    {"symbol": "GOOGL", "company": "Alphabet Inc.", "context": "neutral"}
                ],
                "confidence": 0.90
            }
        else:
            result = {
                "analysis_type": analysis_type,
                "result": "completed",
                "confidence": 0.75
            }
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=result
        )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "content": {"type": "string", "description": "Content to analyze"},
                "analysis_type": {"type": "string", "description": "Type of analysis (sentiment, topics, stocks, etc.)"}
            }
        }


class MockReportGeneratorTool(BaseTool):
    """Mock report generator for demo purposes."""
    
    def __init__(self):
        super().__init__("report_generator", "Generate investment analysis reports")
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute mock report generation."""
        report_type = kwargs.get("report_type", "summary")
        data = kwargs.get("data", {})
        
        mock_report = {
            "report_id": f"report_{hash(str(kwargs))%10000}",
            "type": report_type,
            "title": f"Mock {report_type.title()} Report",
            "content": f"This is a mock {report_type} report generated for demonstration purposes. It would contain comprehensive financial analysis based on the provided data.",
            "generated_at": "2025-08-29T10:00:00Z",
            "data_points": len(str(data))
        }
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=mock_report
        )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "report_type": {"type": "string", "description": "Type of report to generate"},
                "data": {"type": "object", "description": "Data to include in the report"}
            }
        }


class MockSlackNotificationTool(BaseTool):
    """Mock Slack notification tool for demo purposes."""
    
    def __init__(self):
        super().__init__("slack_notification", "Send notifications via Slack")
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute mock Slack notification."""
        message = kwargs.get("message", "Mock notification")
        channel = kwargs.get("channel", "general")
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "notification_sent": True,
                "channel": channel,
                "message_id": f"msg_{hash(message)%10000}",
                "timestamp": "2025-08-29T10:00:00Z"
            }
        )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "parameters": {
                "message": {"type": "string", "description": "Message to send"},
                "channel": {"type": "string", "description": "Slack channel to send to"}
            }
        }


class LLMAnalysisAgent(BaseLLMAgent):
    """
    LLM-powered Analysis Agent for intelligent financial content analysis.
    
    This agent can understand natural language requests and intelligently:
    - Perform sentiment analysis on financial news and content
    - Extract and classify topics, themes, and industry sectors
    - Identify stock mentions and company references
    - Generate comprehensive investment research reports
    - Create vector embeddings for semantic search
    - Provide market insights and trend analysis
    - Handle complex analytical workflows with multi-step reasoning
    
    Examples of tasks it can handle:
    - "Analyze the sentiment of recent Tesla news articles"
    - "Extract key topics from Apple's latest earnings report"
    - "Generate a market summary report for the tech sector"
    - "Find similar articles about renewable energy investments"
    - "Create alerts for negative sentiment about banking stocks"
    """
    
    def __init__(
        self, 
        repository: Optional[UnifiedDatabaseRepository] = None,
        llm: Optional[ChatOpenAI] = None,
        enable_notifications: bool = False,
        confidence_threshold: float = 0.7
    ):
        # Initialize repository if not provided
        self.repository = repository or UnifiedDatabaseRepository()
        
        # Initialize real tools (same as DataAgent for consistency)
        tools = [
            MockOpenAIAnalysisTool(),
            MockReportGeneratorTool(),
            DatabaseStorage(self.repository),
            VectorStorage(self.repository)
        ]
        
        # Add notification tools if enabled
        if enable_notifications:
            tools.append(MockSlackNotificationTool())
        
        # Use different LLM model for analysis
        if llm is None:
            analysis_llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL_ANALYSIS", "gpt-4o"),
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            analysis_llm = llm
        
        super().__init__(
            name="AnalysisAgent",
            description="I am an intelligent financial analyst specialized in content analysis, sentiment detection, and market insights",
            tools=tools,
            llm=analysis_llm,
            memory_window=20,
            max_iterations=25
        )
        
        self.repository = repository
        self.confidence_threshold = confidence_threshold
        self.enable_notifications = enable_notifications
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the AnalysisAgent's specialized prompt."""
        return ChatPromptTemplate.from_template("""You are AnalysisAgent, an expert AI financial analyst specialized in content analysis and market insights.

Your core capabilities include:
- Advanced sentiment analysis with confidence scoring and contextual understanding
- Multi-level topic extraction and thematic analysis across financial content
- Stock and company mention identification with relevance scoring
- Investment research report generation with actionable insights
- Market trend analysis and pattern recognition across time periods
- Vector similarity search and content clustering for related analysis
- Risk assessment and opportunity identification from news and data
- Event impact analysis and correlation detection across markets
- Cross-market and sector analysis with comparative insights
- Technical and fundamental analysis integration
- Real-time market sentiment monitoring and alerting
- Automated insight generation with confidence metrics

You have access to these tools: {tools}
Tool names: {tool_names}

When given an analysis task:
1. Carefully examine the content or request to understand the analytical objective
2. Choose the most appropriate analysis methods and tools for the task
3. Execute analysis step by step, building upon previous results
4. Provide detailed insights with confidence scores and supporting evidence
5. Generate actionable recommendations based on the analysis
6. Handle uncertainty gracefully and indicate confidence levels

Always provide thorough analysis with clear reasoning and quantified confidence levels.

User input: {input}
Agent scratchpad: {agent_scratchpad}""")
    
    def get_capabilities(self) -> List[str]:
        """Get list of AnalysisAgent capabilities."""
        return [
            "analyze_news: Comprehensive analysis of news content (sentiment, topics, stocks)",
            "analyze_sentiment: Sentiment analysis of text content",
            "extract_topics: Extract topics and keywords from content", 
            "generate_report: Generate investment analysis reports",
            "batch_analyze: Batch analysis of multiple news articles",
            "create_embeddings: Create and store vector embeddings (planned)"
        ]
    
    # Convenience methods for common analysis operations
    
    async def analyze_sentiment(
        self, 
        content: str,
        analysis_depth: str = "comprehensive"
    ) -> LLMAgentResult:
        """Convenience method for sentiment analysis using natural language."""
        task = LLMAgentTask(
            task_id=f"sentiment_{hash(content[:100])%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Perform {analysis_depth} sentiment analysis on the provided financial content, including confidence scoring and contextual insights",
            parameters={
                "content": content,
                "analysis_type": "sentiment",
                "depth": analysis_depth
            }
        )
        return await self.execute_task(task)
    
    async def extract_topics(
        self, 
        content: str,
        max_topics: int = 10
    ) -> LLMAgentResult:
        """Convenience method for topic extraction using natural language."""
        task = LLMAgentTask(
            task_id=f"topics_{hash(content[:100])%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Extract up to {max_topics} key topics, themes, and keywords from the financial content with relevance scoring",
            parameters={
                "content": content,
                "analysis_type": "topics", 
                "max_topics": max_topics
            }
        )
        return await self.execute_task(task)
    
    async def identify_stocks(
        self, 
        content: str,
        include_context: bool = True
    ) -> LLMAgentResult:
        """Convenience method for stock mention identification using natural language."""
        task = LLMAgentTask(
            task_id=f"stocks_{hash(content[:100])%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Identify all stock and company mentions in the content{'with contextual sentiment analysis' if include_context else ''}",
            parameters={
                "content": content,
                "analysis_type": "stocks",
                "include_context": include_context
            }
        )
        return await self.execute_task(task)
    
    async def generate_report(
        self, 
        data: Dict[str, Any],
        report_type: str = "summary",
        include_recommendations: bool = True
    ) -> LLMAgentResult:
        """Convenience method for report generation using natural language."""
        task = LLMAgentTask(
            task_id=f"report_{hash(str(data))%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Generate a comprehensive {report_type} report based on the analysis data{'with actionable investment recommendations' if include_recommendations else ''}",
            parameters={
                "data": data,
                "report_type": report_type,
                "include_recommendations": include_recommendations
            }
        )
        return await self.execute_task(task)
    
    async def batch_analyze_news(
        self, 
        articles: List[Dict[str, Any]],
        analysis_types: List[str] = None
    ) -> LLMAgentResult:
        """Convenience method for batch news analysis using natural language."""
        if analysis_types is None:
            analysis_types = ["sentiment", "topics", "stocks"]
        
        task = LLMAgentTask(
            task_id=f"batch_{hash(str(articles))%10000}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=f"Perform comprehensive batch analysis of {len(articles)} news articles including {', '.join(analysis_types)} analysis with aggregated insights",
            parameters={
                "articles": articles,
                "analysis_types": analysis_types,
                "batch_processing": True
            }
        )
        return await self.execute_task(task)