"""
Base Tool class for Agent-Tool architecture.

Provides the foundation for all tools that can be used by agents.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class ToolStatus(Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """Result of tool execution."""
    status: ToolStatus
    data: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """Check if tool execution had an error."""
        return self.status == ToolStatus.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Tools are discrete capabilities that can be used by agents.
    Each tool has a specific purpose and well-defined interface.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult: Result of tool execution
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the parameter schema for this tool.
        
        Returns:
            Dictionary describing required and optional parameters
        """
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate parameters against the tool schema.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        schema = self.get_schema()
        required = schema.get("required", [])
        
        # Check required parameters
        for param in required:
            if param not in kwargs:
                raise ValueError(f"Required parameter '{param}' is missing")
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "schema": self.get_schema()
        }
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """
        Safely execute the tool with error handling.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult: Result with error handling
        """
        try:
            # Validate parameters
            self.validate_parameters(**kwargs)
            
            # Execute the tool
            return await self.execute(**kwargs)
            
        except ValueError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Parameter validation error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error_message=f"Tool execution error: {str(e)}"
            )
    
    def __str__(self) -> str:
        return f"Tool({self.name}): {self.description}"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"