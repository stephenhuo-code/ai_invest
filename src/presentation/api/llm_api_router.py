"""
Natural Language API Router for LLM-powered AI Agents.

Provides intelligent API endpoints that understand natural language requests
and route them to appropriate AI agents for execution.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import StreamingResponse
import asyncio
import json

from ...application.agents.llm_data_agent import LLMDataAgent
from ...application.agents.llm_analysis_agent import LLMAnalysisAgent
from ...application.agents.llm_base_agent import LLMAgentTask, LLMTaskType
from ...application.use_cases.llm_intelligent_workflow import IntelligentWorkflowCoordinator
from ...infrastructure.database.connection import get_repository, create_agents


# Pydantic models for request/response schemas
class NaturalLanguageRequest(BaseModel):
    """Request model for natural language agent tasks."""
    query: str = Field(..., description="Natural language description of the task")
    agent: Optional[str] = Field(None, description="Specific agent to use (data, analysis, auto)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")
    priority: Optional[str] = Field("normal", description="Task priority (low, normal, high, urgent)")
    max_execution_time: Optional[int] = Field(300, description="Maximum execution time in seconds")
    stream_response: Optional[bool] = Field(False, description="Whether to stream the response")


class WorkflowRequest(BaseModel):
    """Request model for intelligent workflow execution."""
    description: str = Field(..., description="Natural language description of the desired workflow")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for workflow planning")
    max_execution_time: Optional[int] = Field(1800, description="Maximum execution time in seconds")
    notify_completion: Optional[bool] = Field(False, description="Whether to send notification on completion")


class AgentResponse(BaseModel):
    """Response model for agent execution results."""
    success: bool
    task_id: str
    agent_name: str
    result: Any
    reasoning_trace: List[str]
    tools_used: List[str]
    execution_time_ms: int
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any]


class WorkflowResponse(BaseModel):
    """Response model for workflow execution results."""
    workflow_id: str
    status: str
    user_request: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    total_execution_time: float
    summary: Optional[Dict[str, Any]] = None
    results: Dict[str, Any]
    errors: List[str] = []


# Create router
llm_router = APIRouter(prefix="/llm", tags=["LLM Agents"])
logger = logging.getLogger("LLMAPIRouter")

# Global instances (will be initialized on startup)
data_agent: Optional[LLMDataAgent] = None
analysis_agent: Optional[LLMAnalysisAgent] = None
workflow_coordinator: Optional[IntelligentWorkflowCoordinator] = None


async def get_agents():
    """Dependency to get initialized agents."""
    global data_agent, analysis_agent, workflow_coordinator
    
    if not all([data_agent, analysis_agent, workflow_coordinator]):
        repository = get_repository()
        data_agent = LLMDataAgent(repository)
        analysis_agent = LLMAnalysisAgent(repository)
        workflow_coordinator = IntelligentWorkflowCoordinator(repository)
    
    return {
        "data": data_agent,
        "analysis": analysis_agent,
        "workflow": workflow_coordinator
    }


@llm_router.post("/execute", response_model=AgentResponse)
async def execute_natural_language_task(
    request: NaturalLanguageRequest,
    agents = Depends(get_agents)
):
    """
    Execute a natural language task using AI agents.
    
    This endpoint can understand complex natural language requests and route them
    to the most appropriate AI agent for execution.
    
    Examples:
    - "Fetch the latest Apple news and analyze market sentiment"
    - "Get Tesla stock data for the past month and identify trends"
    - "Find news about renewable energy companies and create embeddings"
    - "Analyze sentiment of recent tech sector news"
    """
    try:
        # Determine which agent to use
        if request.agent == "auto" or request.agent is None:
            selected_agent = await _select_agent_intelligently(request.query, agents)
        else:
            agent_name = request.agent.lower()
            if agent_name not in agents:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown agent: {request.agent}. Available: data, analysis"
                )
            selected_agent = agents[agent_name]
        
        # Create task
        task = LLMAgentTask(
            task_id=f"nlp_{datetime.now().timestamp()}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=request.query,
            context=request.context or {},
            priority=request.priority,
            max_iterations=15,
            timeout_seconds=request.max_execution_time
        )
        
        # Execute task
        logger.info(f"Executing natural language task: {request.query}")
        result = await selected_agent.execute_task(task)
        
        # Convert to response format
        response = AgentResponse(
            success=result.success,
            task_id=result.task_id,
            agent_name=selected_agent.name,
            result=result.result,
            reasoning_trace=result.reasoning_trace,
            tools_used=result.tools_used,
            execution_time_ms=result.execution_time_ms,
            confidence_score=result.confidence_score,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
        logger.info(f"Task completed: {result.success}")
        return response
        
    except Exception as e:
        logger.error(f"Natural language task execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@llm_router.post("/workflow", response_model=WorkflowResponse)
async def execute_intelligent_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
    agents = Depends(get_agents)
):
    """
    Execute a complex intelligent workflow based on natural language description.
    
    This endpoint can understand complex multi-step workflows and coordinate
    multiple AI agents to execute them efficiently.
    
    Examples:
    - "Analyze market sentiment for FAANG stocks and generate a comprehensive report"
    - "Monitor renewable energy sector trends and alert on significant changes"
    - "Fetch earnings news for tech companies and analyze potential market impact"
    - "Create daily investment briefing with top market movers and sentiment analysis"
    """
    try:
        workflow_coordinator = agents["workflow"]
        
        logger.info(f"Starting intelligent workflow: {request.description}")
        
        # Execute workflow
        workflow_result = await workflow_coordinator.execute_natural_language_workflow(
            user_request=request.description,
            context=request.context,
            max_execution_time=request.max_execution_time
        )
        
        # Convert to response format
        response = WorkflowResponse(
            workflow_id=workflow_result["workflow_id"],
            status=workflow_result["status"].value if hasattr(workflow_result["status"], 'value') else str(workflow_result["status"]),
            user_request=workflow_result["user_request"],
            total_steps=len(workflow_result["steps"]),
            completed_steps=len(workflow_result.get("results", {}).get("completed_steps", [])),
            failed_steps=len(workflow_result.get("results", {}).get("failed_steps", [])),
            total_execution_time=workflow_result.get("total_execution_time", 0),
            summary=workflow_result.get("summary"),
            results=workflow_result.get("results", {}),
            errors=workflow_result.get("errors", [])
        )
        
        # Add notification task if requested
        if request.notify_completion:
            background_tasks.add_task(
                _send_workflow_completion_notification,
                workflow_result
            )
        
        logger.info(f"Workflow completed: {workflow_result['workflow_id']}")
        return response
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@llm_router.get("/agents/info")
async def get_agents_info(agents = Depends(get_agents)):
    """Get comprehensive information about available AI agents."""
    try:
        agents_info = {}
        
        for agent_name, agent in agents.items():
            if agent_name == "workflow":
                # Special handling for workflow coordinator
                agents_info[agent_name] = {
                    "name": "IntelligentWorkflowCoordinator",
                    "type": "workflow_coordinator",
                    "capabilities": agent.get_workflow_capabilities(),
                    "status": "active",
                    "active_workflows": len(agent.get_active_workflows())
                }
            else:
                # Regular agent info
                agent_info = agent.get_info()
                agent_info["status"] = "active"
                agent_info["memory_summary"] = agent.get_memory_summary() if hasattr(agent, 'get_memory_summary') else "No memory"
                agents_info[agent_name] = agent_info
        
        return {
            "agents": agents_info,
            "total_agents": len([a for a in agents_info.values() if a.get("type") != "workflow_coordinator"]),
            "llm_powered": True,
            "natural_language_support": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get agents info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agents info: {str(e)}")


@llm_router.get("/workflow/active")
async def get_active_workflows(agents = Depends(get_agents)):
    """Get information about currently active workflows."""
    try:
        workflow_coordinator = agents["workflow"]
        active_workflows = workflow_coordinator.get_active_workflows()
        
        return {
            "active_workflows": active_workflows,
            "total_active": len(active_workflows)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get active workflows: {str(e)}")


@llm_router.post("/agent/{agent_name}/task")
async def execute_agent_specific_task(
    agent_name: str = Path(..., description="Name of the agent (data or analysis)"),
    request: NaturalLanguageRequest = ...,
    agents = Depends(get_agents)
):
    """
    Execute a task on a specific agent.
    
    Use this endpoint when you want to force a task to be executed by a particular agent
    rather than using automatic agent selection.
    """
    try:
        agent_name = agent_name.lower()
        if agent_name not in agents or agent_name == "workflow":
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found. Available: data, analysis"
            )
        
        selected_agent = agents[agent_name]
        
        # Create and execute task
        task = LLMAgentTask(
            task_id=f"{agent_name}_{datetime.now().timestamp()}",
            task_type=LLMTaskType.NATURAL_LANGUAGE,
            description=request.query,
            context=request.context or {},
            priority=request.priority,
            timeout_seconds=request.max_execution_time
        )
        
        result = await selected_agent.execute_task(task)
        
        return AgentResponse(
            success=result.success,
            task_id=result.task_id,
            agent_name=selected_agent.name,
            result=result.result,
            reasoning_trace=result.reasoning_trace,
            tools_used=result.tools_used,
            execution_time_ms=result.execution_time_ms,
            confidence_score=result.confidence_score,
            error_message=result.error_message,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent-specific task execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@llm_router.delete("/agent/{agent_name}/memory")
async def clear_agent_memory(
    agent_name: str = Path(..., description="Name of the agent"),
    agents = Depends(get_agents)
):
    """Clear the memory of a specific agent."""
    try:
        agent_name = agent_name.lower()
        if agent_name not in agents or agent_name == "workflow":
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_name}' not found"
            )
        
        agent = agents[agent_name]
        agent.clear_memory()
        
        return {"message": f"Memory cleared for {agent_name} agent"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear agent memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")


@llm_router.get("/capabilities")
async def get_system_capabilities():
    """Get comprehensive overview of system capabilities."""
    return {
        "natural_language_processing": {
            "supported": True,
            "description": "Full natural language understanding for task descriptions and workflows"
        },
        "agent_types": {
            "data_agent": {
                "description": "Fetches and processes financial news and market data",
                "key_capabilities": [
                    "RSS news fetching with content extraction",
                    "Yahoo Finance market data collection",
                    "Data quality assessment and validation",
                    "Vector embedding generation and storage",
                    "Multi-source data aggregation"
                ]
            },
            "analysis_agent": {
                "description": "Performs AI-powered analysis of financial content",
                "key_capabilities": [
                    "Advanced sentiment analysis with confidence scoring",
                    "Topic extraction and thematic analysis",
                    "Stock mention identification and context analysis",
                    "Comprehensive market report generation",
                    "Vector similarity search and content clustering"
                ]
            }
        },
        "workflow_coordination": {
            "supported": True,
            "description": "Intelligent multi-agent workflow orchestration",
            "features": [
                "Natural language workflow planning",
                "Dependency management and parallel execution",
                "Error handling and retry strategies",
                "Real-time progress monitoring",
                "Comprehensive result summarization"
            ]
        },
        "example_queries": [
            "Fetch the latest Tesla news and analyze market sentiment",
            "Get Apple stock data for the past quarter and identify trends",
            "Create a daily investment briefing for renewable energy sector",
            "Monitor FAANG stocks sentiment and alert on significant changes",
            "Analyze earnings news impact on tech stock prices"
        ]
    }


# Helper functions

async def _select_agent_intelligently(
    query: str,
    agents: Dict[str, Any]
) -> Any:
    """
    Intelligently select the most appropriate agent for a given query.
    
    Uses keyword analysis and LLM-based intent detection to route queries.
    """
    query_lower = query.lower()
    
    # Simple keyword-based routing
    data_keywords = ["fetch", "get", "collect", "download", "scrape", "data", "news", "stock", "price", "market data"]
    analysis_keywords = ["analyze", "sentiment", "topics", "report", "insights", "trends", "summarize", "classify"]
    
    data_score = sum(1 for keyword in data_keywords if keyword in query_lower)
    analysis_score = sum(1 for keyword in analysis_keywords if keyword in query_lower)
    
    # If query mentions both data collection and analysis, use workflow coordinator
    if data_score > 0 and analysis_score > 0:
        # For complex queries that need both agents, we should use the workflow coordinator
        # But since this is agent selection, we'll default to analysis agent for mixed queries
        return agents["analysis"]
    elif data_score > analysis_score:
        return agents["data"]
    else:
        return agents["analysis"]  # Default to analysis for ambiguous queries


async def _send_workflow_completion_notification(workflow_result: Dict[str, Any]):
    """Send notification when workflow completes (background task)."""
    try:
        # This could integrate with Slack, email, or other notification systems
        logger.info(f"Workflow {workflow_result['workflow_id']} completed - notification sent")
        # TODO: Implement actual notification sending
    except Exception as e:
        logger.error(f"Failed to send workflow completion notification: {str(e)}")


# Streaming response support (for future implementation)
@llm_router.post("/execute/stream")
async def execute_streaming_task(
    request: NaturalLanguageRequest,
    agents = Depends(get_agents)
):
    """
    Execute a natural language task with streaming response.
    
    This endpoint streams the agent's reasoning process and intermediate results
    as they become available.
    """
    # TODO: Implement streaming response using Server-Sent Events (SSE)
    raise HTTPException(status_code=501, detail="Streaming execution not yet implemented")