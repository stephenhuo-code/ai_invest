"""
LLM-powered Base Agent class for the AI Invest platform.

Provides the foundation for intelligent agents powered by Large Language Models
using LangChain framework for advanced reasoning and tool orchestration.
"""
import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.prompts import ChatPromptTemplate, PromptTemplate
    from langchain.schema import AgentAction, AgentFinish
    from langchain.tools import Tool
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.runnables import RunnablePassthrough
except ImportError as e:
    raise ImportError(f"Required LangChain packages not installed: {e}")

from ..tools.base_tool import BaseTool, ToolResult, ToolStatus


class LLMTaskType(Enum):
    """Types of tasks the LLM agent can handle."""
    NATURAL_LANGUAGE = "natural_language"  # Free-form natural language task
    STRUCTURED = "structured"              # Structured task with specific parameters
    CONVERSATION = "conversation"          # Conversational interaction
    WORKFLOW = "workflow"                  # Complex multi-step workflow


@dataclass
class LLMAgentTask:
    """
    Enhanced task structure for LLM-powered agents.
    
    Supports both natural language descriptions and structured parameters.
    """
    task_id: str
    task_type: LLMTaskType
    description: str  # Natural language description of the task
    parameters: Dict[str, Any] = None  # Optional structured parameters
    context: Dict[str, Any] = None     # Additional context for the task
    priority: str = "normal"           # Task priority: low, normal, high, urgent
    max_iterations: int = 10           # Maximum reasoning iterations
    timeout_seconds: int = 300         # Task timeout
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.context is None:
            self.context = {}


@dataclass 
class LLMAgentResult:
    """Enhanced result structure for LLM agent execution."""
    success: bool
    task_id: str
    result: Any = None
    reasoning_trace: List[str] = None      # LLM reasoning steps
    tools_used: List[str] = None           # Tools that were used
    tokens_used: Dict[str, int] = None     # Token usage statistics
    execution_time_ms: int = 0
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None  # Agent's confidence in the result
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.reasoning_trace is None:
            self.reasoning_trace = []
        if self.tools_used is None:
            self.tools_used = []
        if self.tokens_used is None:
            self.tokens_used = {"prompt": 0, "completion": 0, "total": 0}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "success": self.success,
            "task_id": self.task_id,
            "result": self.result,
            "reasoning_trace": self.reasoning_trace,
            "tools_used": self.tools_used,
            "tokens_used": self.tokens_used,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata
        }


class LangChainToolAdapter:
    """
    Adapter to convert BaseTool instances to LangChain Tools.
    
    This enables seamless integration of existing tools with LangChain agents.
    """
    
    def __init__(self, base_tool: BaseTool):
        self.base_tool = base_tool
        self.logger = logging.getLogger(f"ToolAdapter[{base_tool.name}]")
    
    def create_langchain_tool(self) -> Tool:
        """Create a LangChain Tool from BaseTool."""
        return Tool(
            name=self.base_tool.name,
            description=self._create_tool_description(),
            func=self._sync_execute,
            coroutine=self._async_execute
        )
    
    def _create_tool_description(self) -> str:
        """Create enhanced tool description for LLM."""
        schema = self.base_tool.get_schema()
        
        description = f"{self.base_tool.description}\n\n"
        
        if schema.get("parameters"):
            description += "Parameters:\n"
            for param_name, param_info in schema["parameters"].items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                required = param_name in schema.get("required", [])
                required_str = " (required)" if required else " (optional)"
                description += f"- {param_name} ({param_type}){required_str}: {param_desc}\n"
        
        return description.strip()
    
    def _sync_execute(self, tool_input: str) -> str:
        """Synchronous wrapper for tool execution."""
        try:
            # Parse tool input (could be JSON string or plain text)
            import json
            try:
                params = json.loads(tool_input)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, treat as a single parameter
                params = {"input": tool_input}
            
            # Run the async tool in the event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new task if loop is already running
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.base_tool.execute(**params))
                    result = future.result()
            else:
                result = loop.run_until_complete(self.base_tool.execute(**params))
            
            return self._format_tool_result(result)
            
        except Exception as e:
            self.logger.error(f"Tool execution error: {str(e)}")
            return f"Error executing tool: {str(e)}"
    
    async def _async_execute(self, tool_input: str) -> str:
        """Asynchronous tool execution."""
        try:
            # Parse tool input
            import json
            try:
                params = json.loads(tool_input)
            except (json.JSONDecodeError, TypeError):
                params = {"input": tool_input}
            
            result = await self.base_tool.execute(**params)
            return self._format_tool_result(result)
            
        except Exception as e:
            self.logger.error(f"Async tool execution error: {str(e)}")
            return f"Error executing tool: {str(e)}"
    
    def _format_tool_result(self, result: ToolResult) -> str:
        """Format tool result for LLM consumption."""
        if result.is_success:
            # Format successful result
            if isinstance(result.data, dict):
                return f"Success: {result.data}"
            elif isinstance(result.data, str):
                return result.data
            else:
                return f"Tool executed successfully. Result: {result.data}"
        else:
            return f"Tool failed: {result.error_message}"


class BaseLLMAgent(ABC):
    """
    Base class for LLM-powered intelligent agents.
    
    Integrates LangChain framework for advanced reasoning, memory, and tool orchestration.
    Each agent is specialized for specific domain tasks but can handle natural language instructions.
    """
    
    def __init__(
        self,
        name: str,
        description: str, 
        tools: List[BaseTool],
        llm: Optional[ChatOpenAI] = None,
        memory_window: int = 10,
        max_iterations: int = 15,
        verbose: bool = False
    ):
        self.name = name
        self.description = description
        self.tools = tools
        self.memory_window = memory_window
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Initialize logger
        self.logger = logging.getLogger(f"LLMAgent[{self.name}]")
        
        # Initialize LLM
        if llm is None:
            import os
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL_AGENT", "gpt-4o-mini"),
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = llm
        
        # Setup memory
        self.memory = ConversationBufferWindowMemory(
            k=memory_window,
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Convert tools to LangChain format
        self.langchain_tools = self._convert_tools()
        
        # Create agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.langchain_tools,
            memory=self.memory,
            max_iterations=max_iterations,
            verbose=verbose,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        self.logger = logging.getLogger(f"LLMAgent[{self.name}]")
    
    def _convert_tools(self) -> List[Tool]:
        """Convert BaseTool instances to LangChain Tools."""
        langchain_tools = []
        
        for tool in self.tools:
            adapter = LangChainToolAdapter(tool)
            langchain_tool = adapter.create_langchain_tool()
            langchain_tools.append(langchain_tool)
        
        self.logger.info(f"Converted {len(langchain_tools)} tools for LangChain integration")
        return langchain_tools
    
    def _create_agent(self):
        """Create the LangChain agent with custom prompt."""
        prompt = self._create_agent_prompt()
        return create_react_agent(
            llm=self.llm,
            tools=self.langchain_tools,
            prompt=prompt
        )
    
    @abstractmethod
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """Create the agent's system prompt. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this agent provides."""
        pass
    
    async def execute_task(self, task: LLMAgentTask) -> LLMAgentResult:
        """
        Execute a task using LLM reasoning and tool orchestration.
        
        Args:
            task: The task to execute
            
        Returns:
            LLMAgentResult with execution details
        """
        start_time = time.time()
        self.logger.info(f"Starting LLM task: {task.task_id} - {task.description}")
        
        try:
            # Prepare input for the agent
            agent_input = self._prepare_agent_input(task)
            
            # Execute using LangChain agent
            response = await self.agent_executor.ainvoke(agent_input)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Extract results
            result = LLMAgentResult(
                success=True,
                task_id=task.task_id,
                result=response.get("output"),
                reasoning_trace=self._extract_reasoning_trace(response),
                tools_used=self._extract_tools_used(response),
                execution_time_ms=execution_time,
                metadata={
                    "agent_name": self.name,
                    "task_type": task.task_type.value,
                    "llm_model": self.llm.model_name
                }
            )
            
            self.logger.info(f"Task completed successfully: {task.task_id} ({execution_time}ms)")
            return result
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            self.logger.error(f"Task execution failed: {task.task_id} - {error_msg}")
            
            return LLMAgentResult(
                success=False,
                task_id=task.task_id,
                error_message=error_msg,
                execution_time_ms=execution_time,
                metadata={
                    "agent_name": self.name,
                    "task_type": task.task_type.value,
                    "error_type": type(e).__name__
                }
            )
    
    def _prepare_agent_input(self, task: LLMAgentTask) -> Dict[str, Any]:
        """Prepare input for the LangChain agent."""
        agent_input = {"input": task.description}
        
        # Add context if provided
        if task.context:
            context_str = "\n".join([f"{k}: {v}" for k, v in task.context.items()])
            agent_input["input"] += f"\n\nContext:\n{context_str}"
        
        # Add parameters if provided
        if task.parameters:
            params_str = "\n".join([f"{k}: {v}" for k, v in task.parameters.items()])
            agent_input["input"] += f"\n\nParameters:\n{params_str}"
        
        return agent_input
    
    def _extract_reasoning_trace(self, response: Dict[str, Any]) -> List[str]:
        """Extract reasoning steps from agent response."""
        trace = []
        
        intermediate_steps = response.get("intermediate_steps", [])
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, observation = step
                if isinstance(action, AgentAction):
                    trace.append(f"Action: {action.tool} - {action.tool_input}")
                    trace.append(f"Observation: {observation}")
        
        return trace
    
    def _extract_tools_used(self, response: Dict[str, Any]) -> List[str]:
        """Extract list of tools used from agent response."""
        tools_used = []
        
        intermediate_steps = response.get("intermediate_steps", [])
        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) == 2:
                action, _ = step
                if isinstance(action, AgentAction) and action.tool not in tools_used:
                    tools_used.append(action.tool)
        
        return tools_used
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def get_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            "name": self.name,
            "description": self.description,
            "type": "llm_powered",
            "capabilities": self.get_capabilities(),
            "tools_available": self.get_available_tools(),
            "tool_count": len(self.tools),
            "llm_model": self.llm.model_name,
            "memory_window": self.memory_window,
            "max_iterations": self.max_iterations
        }
    
    def clear_memory(self):
        """Clear the agent's conversation memory."""
        self.memory.clear()
        self.logger.info("Agent memory cleared")
    
    def get_memory_summary(self) -> str:
        """Get a summary of the agent's current memory state."""
        if hasattr(self.memory, 'chat_memory') and self.memory.chat_memory.messages:
            return f"Memory contains {len(self.memory.chat_memory.messages)} messages"
        return "Memory is empty"
    
    def __str__(self) -> str:
        return f"LLMAgent({self.name}): {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', tools={len(self.tools)}, llm='{self.llm.model_name}')>"