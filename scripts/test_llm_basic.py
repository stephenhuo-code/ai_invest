#!/usr/bin/env python3
"""
Basic test script for LLM Agent architecture validation.

Tests the core components without requiring full workflow execution.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_imports():
    """Test if all LLM agent modules can be imported successfully."""
    print("🔍 Testing LLM Agent imports...")
    
    try:
        # Test core agent imports
        from src.application.agents.llm_base_agent import BaseLLMAgent, LLMAgentTask, LLMAgentResult
        print("  ✅ BaseLLMAgent imported successfully")
        
        from src.application.agents.llm_data_agent import LLMDataAgent
        print("  ✅ LLMDataAgent imported successfully")
        
        from src.application.agents.llm_analysis_agent import LLMAnalysisAgent
        print("  ✅ LLMAnalysisAgent imported successfully")
        
        from src.application.agents.memory_manager import EnhancedMemoryManager
        print("  ✅ EnhancedMemoryManager imported successfully")
        
        from src.application.use_cases.llm_intelligent_workflow import IntelligentWorkflowCoordinator
        print("  ✅ IntelligentWorkflowCoordinator imported successfully")
        
        from src.presentation.api.llm_api_router import llm_router
        print("  ✅ LLM API router imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False


async def test_langchain_dependencies():
    """Test if LangChain dependencies are available."""
    print("\n📦 Testing LangChain dependencies...")
    
    try:
        from langchain_openai import ChatOpenAI
        print("  ✅ ChatOpenAI available")
        
        from langchain.agents import create_react_agent
        print("  ✅ ReAct agent available")
        
        from langchain.memory import ConversationBufferWindowMemory
        print("  ✅ Conversation memory available")
        
        from langchain.prompts import ChatPromptTemplate
        print("  ✅ Chat prompts available")
        
        from langchain.tools import Tool
        print("  ✅ LangChain tools available")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ LangChain dependency missing: {str(e)}")
        return False


async def test_basic_initialization():
    """Test basic agent initialization without database."""
    print("\n🤖 Testing basic agent initialization...")
    
    try:
        # Import required modules
        from src.application.agents.llm_base_agent import BaseLLMAgent, LLMAgentTask, LLMTaskType
        from src.application.tools.base_tool import BaseTool, ToolResult, ToolStatus
        from langchain_openai import ChatOpenAI
        
        # Create a simple mock tool
        class MockTool(BaseTool):
            def __init__(self):
                super().__init__("mock_tool", "A mock tool for testing")
            
            async def execute(self, **kwargs):
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={"message": "Mock tool executed successfully"}
                )
            
            def get_schema(self):
                return {"parameters": {"input": {"type": "string"}}}
        
        # Create a simple test agent
        class TestAgent(BaseLLMAgent):
            def get_capabilities(self):
                return ["Testing", "Mock operations"]
            
            def _create_agent_prompt(self):
                from langchain.prompts import ChatPromptTemplate
                return ChatPromptTemplate.from_template(
                    "You are a test agent.\n\nAvailable tools: {tools}\nTool names: {tool_names}\n\nTask: {input}\n\nScratchpad: {agent_scratchpad}"
                )
        
        # Test agent creation
        mock_tool = MockTool()
        test_agent = TestAgent(
            name="TestAgent",
            description="A test agent for validation",
            tools=[mock_tool]
        )
        
        print(f"  ✅ Test agent created: {test_agent.name}")
        print(f"     Tools: {test_agent.get_available_tools()}")
        print(f"     LLM Model: {test_agent.llm.model_name}")
        
        # Test tool adaptation
        if hasattr(test_agent, 'langchain_tools'):
            print(f"     LangChain tools: {len(test_agent.langchain_tools)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Basic initialization failed: {str(e)}")
        return False


async def test_memory_system():
    """Test the memory management system."""
    print("\n🧠 Testing memory management system...")
    
    try:
        from src.application.agents.memory_manager import EnhancedMemoryManager, MemoryType
        from langchain_openai import ChatOpenAI
        
        # Create memory manager
        memory_manager = EnhancedMemoryManager(
            agent_name="TestAgent",
            llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1),
            max_conversation_memory=5
        )
        
        # Test memory operations
        memory_manager.add_conversation_message("Hello, how are you?", is_human=True)
        memory_manager.add_conversation_message("I'm doing well, thank you!", is_human=False)
        
        memory_manager.add_context("test_context", {"value": "test data"})
        memory_manager.add_knowledge("Test knowledge item", "testing", confidence=0.9)
        
        # Get memory summary
        summary = memory_manager.get_memory_summary()
        print(f"  ✅ Memory system working")
        print(f"     Total memories: {summary['total_memories']}")
        print(f"     Conversation messages: {summary['conversation_messages']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Memory system test failed: {str(e)}")
        return False


async def main():
    """Run basic validation tests."""
    print("🚀 LLM Agent Basic Validation Test")
    print("="*50)
    
    tests = [
        ("Import Test", test_imports),
        ("LangChain Dependencies", test_langchain_dependencies),
        ("Basic Initialization", test_basic_initialization),
        ("Memory System", test_memory_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! LLM Agent architecture is ready.")
        print("\nNext steps:")
        print("- Set OPENAI_API_KEY in your .env file")
        print("- Run the full test suite: python scripts/test_llm_agents.py")
        print("- Start the application: uvicorn main:app --reload")
        print("- Test LLM endpoints at: http://localhost:8000/llm/")
        return True
    else:
        print("❌ Some basic tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)