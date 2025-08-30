"""
Advanced Memory Management System for LLM Agents.

Provides sophisticated memory capabilities including conversation memory,
task history, context summarization, and persistent storage.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryBufferMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import BaseMessage as CoreBaseMessage
except ImportError as e:
    raise ImportError(f"Required LangChain packages not installed: {e}")

from .llm_base_agent import LLMAgentResult


class MemoryType(Enum):
    """Types of memory storage."""
    CONVERSATION = "conversation"      # Chat history and interactions
    TASK_HISTORY = "task_history"     # Completed tasks and results
    CONTEXT = "context"               # Domain-specific context
    KNOWLEDGE = "knowledge"           # Learned facts and insights
    PREFERENCE = "preference"         # User preferences and settings


@dataclass
class MemoryEntry:
    """Individual memory entry with metadata."""
    entry_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    timestamp: datetime
    agent_name: str
    importance: float = 0.5  # 0-1 scale for memory importance
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        data["memory_type"] = MemoryType(data["memory_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data["last_accessed"]:
            data["last_accessed"] = datetime.fromisoformat(data["last_accessed"])
        return cls(**data)


class EnhancedMemoryManager:
    """
    Advanced memory management system for LLM agents.
    
    Features:
    - Multi-type memory storage (conversation, tasks, context, knowledge)
    - Importance-based memory retention
    - Automatic summarization of long conversations
    - Context-aware memory retrieval
    - Persistent storage support
    - Memory optimization and cleanup
    """
    
    def __init__(
        self,
        agent_name: str,
        llm: Optional[ChatOpenAI] = None,
        max_conversation_memory: int = 20,
        max_task_history: int = 50,
        max_context_entries: int = 100,
        enable_summarization: bool = True,
        importance_threshold: float = 0.3
    ):
        self.agent_name = agent_name
        self.max_conversation_memory = max_conversation_memory
        self.max_task_history = max_task_history
        self.max_context_entries = max_context_entries
        self.enable_summarization = enable_summarization
        self.importance_threshold = importance_threshold
        
        self.logger = logging.getLogger(f"MemoryManager[{agent_name}]")
        
        # Initialize LLM for summarization
        if llm is None:
            import os
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL_MEMORY", "gpt-3.5-turbo"),
                temperature=0.1,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = llm
        
        # Memory storage
        self.memories: Dict[MemoryType, List[MemoryEntry]] = {
            memory_type: [] for memory_type in MemoryType
        }
        
        # LangChain memory components
        if enable_summarization:
            self.conversation_memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000,
                return_messages=True,
                memory_key="chat_history"
            )
        else:
            self.conversation_memory = ConversationBufferWindowMemory(
                k=max_conversation_memory,
                return_messages=True,
                memory_key="chat_history"
            )
        
        self.logger.info(f"Memory manager initialized for {agent_name}")
    
    def add_conversation_message(self, message: str, is_human: bool = True) -> None:
        """Add a conversation message to memory."""
        if is_human:
            self.conversation_memory.chat_memory.add_user_message(message)
        else:
            self.conversation_memory.chat_memory.add_ai_message(message)
        
        # Also store as memory entry
        entry = MemoryEntry(
            entry_id=f"conv_{datetime.now().timestamp()}",
            memory_type=MemoryType.CONVERSATION,
            content={
                "message": message,
                "is_human": is_human,
                "speaker": "Human" if is_human else self.agent_name
            },
            timestamp=datetime.now(),
            agent_name=self.agent_name,
            importance=self._calculate_message_importance(message)
        )
        
        self._add_memory_entry(entry)
    
    def add_task_result(self, task_id: str, result: LLMAgentResult) -> None:
        """Add a completed task result to memory."""
        entry = MemoryEntry(
            entry_id=f"task_{task_id}",
            memory_type=MemoryType.TASK_HISTORY,
            content={
                "task_id": task_id,
                "success": result.success,
                "result": result.result,
                "tools_used": result.tools_used,
                "execution_time_ms": result.execution_time_ms,
                "reasoning_trace": result.reasoning_trace[:5] if result.reasoning_trace else [],  # Keep first 5 steps
                "error_message": result.error_message
            },
            timestamp=datetime.now(),
            agent_name=self.agent_name,
            importance=self._calculate_task_importance(result),
            tags=["task", "completed", "success" if result.success else "failed"]
        )
        
        self._add_memory_entry(entry)
        self.logger.debug(f"Added task result to memory: {task_id}")
    
    def add_context(self, context_key: str, context_value: Any, importance: float = 0.5) -> None:
        """Add contextual information to memory."""
        entry = MemoryEntry(
            entry_id=f"context_{context_key}_{datetime.now().timestamp()}",
            memory_type=MemoryType.CONTEXT,
            content={
                "key": context_key,
                "value": context_value,
                "data_type": type(context_value).__name__
            },
            timestamp=datetime.now(),
            agent_name=self.agent_name,
            importance=importance,
            tags=["context", context_key]
        )
        
        self._add_memory_entry(entry)
    
    def add_knowledge(self, knowledge_item: str, source: str = "learning", confidence: float = 0.8) -> None:
        """Add learned knowledge to memory."""
        entry = MemoryEntry(
            entry_id=f"knowledge_{hash(knowledge_item)%10000}",
            memory_type=MemoryType.KNOWLEDGE,
            content={
                "knowledge": knowledge_item,
                "source": source,
                "confidence": confidence
            },
            timestamp=datetime.now(),
            agent_name=self.agent_name,
            importance=confidence,
            tags=["knowledge", source]
        )
        
        self._add_memory_entry(entry)
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history."""
        messages = self.conversation_memory.chat_memory.messages
        if not messages:
            return "No conversation history available."
        
        history = []
        for message in messages[-10:]:  # Get last 10 messages
            if isinstance(message, HumanMessage):
                history.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                history.append(f"Assistant: {message.content}")
            elif isinstance(message, SystemMessage):
                history.append(f"System: {message.content}")
        
        return "\n".join(history)
    
    def get_recent_tasks(self, limit: int = 5, success_only: bool = False) -> List[Dict[str, Any]]:
        """Get recent task results."""
        task_memories = self.memories[MemoryType.TASK_HISTORY]
        
        if success_only:
            task_memories = [m for m in task_memories if m.content.get("success", False)]
        
        # Sort by timestamp and get most recent
        recent_tasks = sorted(task_memories, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "task_id": task.content["task_id"],
                "success": task.content["success"],
                "tools_used": task.content["tools_used"],
                "execution_time_ms": task.content["execution_time_ms"],
                "timestamp": task.timestamp.isoformat(),
                "importance": task.importance
            }
            for task in recent_tasks
        ]
    
    def get_relevant_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Get contextually relevant memory entries."""
        relevant_memories = []
        
        # Simple relevance scoring based on keyword matching
        query_words = set(query.lower().split())
        
        for memory_type, memories in self.memories.items():
            for memory in memories:
                relevance_score = self._calculate_relevance(memory, query_words)
                if relevance_score > 0.1:  # Minimum relevance threshold
                    relevant_memories.append((memory, relevance_score))
        
        # Sort by relevance and importance
        relevant_memories.sort(key=lambda x: x[1] * x[0].importance, reverse=True)
        
        return [
            {
                "content": memory.content,
                "type": memory.memory_type.value,
                "importance": memory.importance,
                "relevance": relevance,
                "timestamp": memory.timestamp.isoformat()
            }
            for memory, relevance in relevant_memories[:max_results]
        ]
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        total_memories = sum(len(memories) for memories in self.memories.values())
        
        return {
            "agent_name": self.agent_name,
            "total_memories": total_memories,
            "memory_breakdown": {
                memory_type.value: len(memories)
                for memory_type, memories in self.memories.items()
            },
            "conversation_messages": len(self.conversation_memory.chat_memory.messages),
            "high_importance_memories": sum(
                1 for memories in self.memories.values()
                for memory in memories if memory.importance > 0.8
            ),
            "memory_age_days": {
                "oldest": (datetime.now() - min(
                    (memory.timestamp for memories in self.memories.values() for memory in memories),
                    default=datetime.now()
                )).days,
                "newest": 0
            }
        }
    
    def optimize_memory(self, force_cleanup: bool = False) -> Dict[str, int]:
        """Optimize memory usage by removing low-importance entries."""
        cleanup_stats = {"removed": 0, "summarized": 0, "retained": 0}
        
        for memory_type, memories in self.memories.items():
            max_size = self._get_max_size_for_type(memory_type)
            
            if len(memories) > max_size or force_cleanup:
                # Sort by importance and recency
                memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
                
                # Remove low-importance old entries
                to_remove = []
                for i, memory in enumerate(memories):
                    if (i >= max_size or 
                        (memory.importance < self.importance_threshold and 
                         (datetime.now() - memory.timestamp).days > 7)):
                        to_remove.append(memory)
                
                for memory in to_remove:
                    memories.remove(memory)
                    cleanup_stats["removed"] += 1
        
        # Summarize old conversations if enabled
        if self.enable_summarization and len(self.conversation_memory.chat_memory.messages) > 30:
            # The ConversationSummaryBufferMemory will automatically summarize
            cleanup_stats["summarized"] += 1
        
        cleanup_stats["retained"] = sum(len(memories) for memories in self.memories.values())
        
        self.logger.info(f"Memory optimization completed: {cleanup_stats}")
        return cleanup_stats
    
    def clear_memory(self, memory_types: Optional[List[MemoryType]] = None) -> None:
        """Clear specified memory types or all memory."""
        if memory_types is None:
            memory_types = list(MemoryType)
        
        for memory_type in memory_types:
            if memory_type in self.memories:
                cleared_count = len(self.memories[memory_type])
                self.memories[memory_type].clear()
                self.logger.info(f"Cleared {cleared_count} {memory_type.value} memories")
        
        if MemoryType.CONVERSATION in memory_types:
            self.conversation_memory.clear()
    
    def export_memory(self) -> Dict[str, Any]:
        """Export all memory data for persistence."""
        return {
            "agent_name": self.agent_name,
            "export_timestamp": datetime.now().isoformat(),
            "conversation_messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()  # Approximate
                }
                for msg in self.conversation_memory.chat_memory.messages
            ],
            "memories": {
                memory_type.value: [memory.to_dict() for memory in memories]
                for memory_type, memories in self.memories.items()
            }
        }
    
    def import_memory(self, memory_data: Dict[str, Any]) -> bool:
        """Import memory data from exported format."""
        try:
            # Import structured memories
            for memory_type_str, memories_data in memory_data.get("memories", {}).items():
                memory_type = MemoryType(memory_type_str)
                for memory_dict in memories_data:
                    memory = MemoryEntry.from_dict(memory_dict)
                    self.memories[memory_type].append(memory)
            
            # Import conversation messages
            for msg_data in memory_data.get("conversation_messages", []):
                if msg_data["type"] == "HumanMessage":
                    self.conversation_memory.chat_memory.add_user_message(msg_data["content"])
                elif msg_data["type"] == "AIMessage":
                    self.conversation_memory.chat_memory.add_ai_message(msg_data["content"])
            
            self.logger.info("Memory data imported successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import memory data: {str(e)}")
            return False
    
    # Private helper methods
    
    def _add_memory_entry(self, entry: MemoryEntry) -> None:
        """Add memory entry with automatic optimization."""
        self.memories[entry.memory_type].append(entry)
        
        # Auto-optimize if memory gets too large
        max_size = self._get_max_size_for_type(entry.memory_type)
        if len(self.memories[entry.memory_type]) > max_size * 1.2:
            self.optimize_memory()
    
    def _get_max_size_for_type(self, memory_type: MemoryType) -> int:
        """Get maximum size for each memory type."""
        size_limits = {
            MemoryType.CONVERSATION: self.max_conversation_memory,
            MemoryType.TASK_HISTORY: self.max_task_history,
            MemoryType.CONTEXT: self.max_context_entries,
            MemoryType.KNOWLEDGE: 200,
            MemoryType.PREFERENCE: 50
        }
        return size_limits.get(memory_type, 100)
    
    def _calculate_message_importance(self, message: str) -> float:
        """Calculate importance score for a conversation message."""
        # Simple heuristics for message importance
        importance = 0.5  # Base importance
        
        # Longer messages might be more important
        if len(message) > 100:
            importance += 0.1
        
        # Questions and requests are important
        if any(word in message.lower() for word in ['?', 'please', 'can you', 'how', 'what', 'why']):
            importance += 0.2
        
        # Financial terms increase importance
        financial_terms = ['stock', 'market', 'investment', 'analysis', 'price', 'trading']
        if any(term in message.lower() for term in financial_terms):
            importance += 0.3
        
        return min(importance, 1.0)
    
    def _calculate_task_importance(self, result: LLMAgentResult) -> float:
        """Calculate importance score for a task result."""
        importance = 0.5  # Base importance
        
        # Successful tasks are more important
        if result.success:
            importance += 0.2
        
        # Complex tasks (more tools used) are more important
        if len(result.tools_used) > 2:
            importance += 0.1
        
        # Long-running tasks might be more important
        if result.execution_time_ms > 30000:  # > 30 seconds
            importance += 0.2
        
        # Tasks with detailed reasoning are more important
        if result.reasoning_trace and len(result.reasoning_trace) > 5:
            importance += 0.1
        
        return min(importance, 1.0)
    
    def _calculate_relevance(self, memory: MemoryEntry, query_words: set) -> float:
        """Calculate relevance score between memory and query."""
        relevance = 0.0
        
        # Check content for keyword matches
        content_text = str(memory.content).lower()
        content_words = set(content_text.split())
        
        # Calculate word overlap
        common_words = query_words.intersection(content_words)
        if common_words:
            relevance = len(common_words) / len(query_words)
        
        # Boost relevance for recent memories
        days_old = (datetime.now() - memory.timestamp).days
        if days_old < 1:
            relevance *= 1.5
        elif days_old < 7:
            relevance *= 1.2
        
        # Boost relevance for high-importance memories
        relevance *= (1 + memory.importance)
        
        return min(relevance, 1.0)