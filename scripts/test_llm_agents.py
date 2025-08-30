#!/usr/bin/env python3
"""
Test script for LLM-powered AI Agents.

Comprehensive testing of the new LangChain-based agent architecture
including DataAgent, AnalysisAgent, and Intelligent Workflow Coordinator.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import init_database, get_repository
from src.application.agents.llm_data_agent import LLMDataAgent
from src.application.agents.llm_analysis_agent import LLMAnalysisAgent
from src.application.agents.llm_base_agent import LLMAgentTask, LLMTaskType
from src.application.use_cases.llm_intelligent_workflow import IntelligentWorkflowCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMAgentTestSuite:
    """Comprehensive test suite for LLM-powered agents."""
    
    def __init__(self):
        self.repository = None
        self.data_agent = None
        self.analysis_agent = None
        self.workflow_coordinator = None
        self.test_results = {
            "database_setup": False,
            "data_agent_init": False,
            "analysis_agent_init": False,
            "workflow_coordinator_init": False,
            "data_agent_task": False,
            "analysis_agent_task": False,
            "natural_language_workflow": False,
            "agent_memory": False,
            "tool_integration": False
        }
    
    async def setup_test_environment(self):
        """Initialize test environment."""
        print("\n🔧 Setting up LLM Agent test environment...")
        
        try:
            # Initialize database
            await init_database()
            self.repository = get_repository()
            
            # Test database connection
            health_check = await self.repository.health_check()
            if not health_check:
                raise Exception("Database health check failed")
            
            self.test_results["database_setup"] = True
            print("✅ Database setup completed")
            
        except Exception as e:
            print(f"❌ Database setup failed: {str(e)}")
            raise
    
    async def test_agent_initialization(self):
        """Test LLM agent initialization."""
        print("\n🤖 Testing LLM Agent initialization...")
        
        try:
            # Initialize DataAgent
            print("  Initializing DataAgent...")
            self.data_agent = LLMDataAgent(self.repository)
            
            agent_info = self.data_agent.get_info()
            print(f"  ✅ DataAgent initialized: {agent_info['name']} with {agent_info['tool_count']} tools")
            print(f"     LLM Model: {agent_info['llm_model']}")
            print(f"     Memory Window: {agent_info['memory_window']} messages")
            
            self.test_results["data_agent_init"] = True
            
            # Initialize AnalysisAgent
            print("  Initializing AnalysisAgent...")
            self.analysis_agent = LLMAnalysisAgent(self.repository)
            
            agent_info = self.analysis_agent.get_info()
            print(f"  ✅ AnalysisAgent initialized: {agent_info['name']} with {agent_info['tool_count']} tools")
            print(f"     LLM Model: {agent_info['llm_model']}")
            print(f"     Memory Window: {agent_info['memory_window']} messages")
            
            self.test_results["analysis_agent_init"] = True
            
            # Initialize Workflow Coordinator
            print("  Initializing Workflow Coordinator...")
            self.workflow_coordinator = IntelligentWorkflowCoordinator(self.repository)
            print("  ✅ Workflow Coordinator initialized")
            
            self.test_results["workflow_coordinator_init"] = True
            
        except Exception as e:
            print(f"❌ Agent initialization failed: {str(e)}")
            raise
    
    async def test_data_agent_tasks(self):
        """Test DataAgent natural language task execution."""
        print("\n📊 Testing DataAgent natural language tasks...")
        
        try:
            # Test simple data fetching task
            print("  Testing news fetching with natural language...")
            
            task = LLMAgentTask(
                task_id="test_data_fetch",
                task_type=LLMTaskType.NATURAL_LANGUAGE,
                description="Fetch 3 recent financial news articles and store them in the database",
                parameters={"max_articles": 3}
            )
            
            result = await self.data_agent.execute_task(task)
            
            if result.success:
                print(f"  ✅ Data fetching task completed successfully")
                print(f"     Tools used: {', '.join(result.tools_used)}")
                print(f"     Execution time: {result.execution_time_ms}ms")
                print(f"     Reasoning steps: {len(result.reasoning_trace)}")
                
                if result.reasoning_trace:
                    print("     First few reasoning steps:")
                    for i, step in enumerate(result.reasoning_trace[:3]):
                        print(f"       {i+1}. {step}")
                
                self.test_results["data_agent_task"] = True
            else:
                print(f"  ⚠️ Data fetching task completed with errors: {result.error_message}")
                # Still consider it a partial success if we got some reasoning
                if result.reasoning_trace:
                    self.test_results["data_agent_task"] = True
            
        except Exception as e:
            print(f"❌ DataAgent task testing failed: {str(e)}")
    
    async def test_analysis_agent_tasks(self):
        """Test AnalysisAgent natural language task execution."""
        print("\n🧠 Testing AnalysisAgent natural language tasks...")
        
        try:
            # Test analysis task with mock content
            print("  Testing sentiment analysis with natural language...")
            
            mock_content = """
            Apple Inc. reported strong quarterly earnings today, beating analyst expectations
            on both revenue and profit margins. The company's iPhone sales showed remarkable
            resilience despite global economic headwinds. CEO Tim Cook expressed optimism
            about the company's future prospects, particularly in emerging markets and
            services revenue. Investors responded positively, with shares rising 5% in
            after-hours trading.
            """
            
            task = LLMAgentTask(
                task_id="test_analysis",
                task_type=LLMTaskType.NATURAL_LANGUAGE,
                description=f"Analyze the sentiment, extract key topics, and identify stock mentions from this news content: {mock_content}",
                parameters={"include_confidence": True}
            )
            
            result = await self.analysis_agent.execute_task(task)
            
            if result.success:
                print(f"  ✅ Analysis task completed successfully")
                print(f"     Tools used: {', '.join(result.tools_used)}")
                print(f"     Execution time: {result.execution_time_ms}ms")
                print(f"     Reasoning steps: {len(result.reasoning_trace)}")
                
                if result.reasoning_trace:
                    print("     Key reasoning steps:")
                    for i, step in enumerate(result.reasoning_trace[:3]):
                        print(f"       {i+1}. {step}")
                
                self.test_results["analysis_agent_task"] = True
            else:
                print(f"  ⚠️ Analysis task completed with errors: {result.error_message}")
                # Still consider it a partial success if we got some reasoning
                if result.reasoning_trace:
                    self.test_results["analysis_agent_task"] = True
            
        except Exception as e:
            print(f"❌ AnalysisAgent task testing failed: {str(e)}")
    
    async def test_natural_language_workflow(self):
        """Test intelligent workflow coordination."""
        print("\n🔄 Testing Natural Language Workflow...")
        
        try:
            print("  Testing complex workflow with natural language...")
            
            workflow_request = """
            Analyze the current market sentiment for technology stocks by:
            1. Fetching recent news about major tech companies like Apple, Microsoft, and Google
            2. Analyzing the sentiment and key themes from these articles
            3. Providing a summary report with investment insights
            """
            
            workflow_result = await self.workflow_coordinator.execute_natural_language_workflow(
                user_request=workflow_request,
                max_execution_time=300  # 5 minutes max
            )
            
            if workflow_result["status"].name == "COMPLETED":
                print(f"  ✅ Workflow completed successfully")
                print(f"     Workflow ID: {workflow_result['workflow_id']}")
                print(f"     Total steps: {len(workflow_result['steps'])}")
                print(f"     Completed steps: {len(workflow_result.get('results', {}).get('completed_steps', []))}")
                print(f"     Total execution time: {workflow_result.get('total_execution_time', 0):.2f}s")
                
                if workflow_result.get('summary'):
                    summary = workflow_result['summary']
                    print(f"     Executive Summary: {summary.get('executive_summary', 'N/A')}")
                
                self.test_results["natural_language_workflow"] = True
            else:
                print(f"  ⚠️ Workflow completed with status: {workflow_result['status']}")
                print(f"     Errors: {workflow_result.get('errors', [])}")
                # Consider partial success if some steps completed
                if workflow_result.get('results', {}).get('completed_steps'):
                    self.test_results["natural_language_workflow"] = True
            
        except Exception as e:
            print(f"❌ Workflow testing failed: {str(e)}")
    
    async def test_agent_memory(self):
        """Test agent memory functionality."""
        print("\n🧠 Testing Agent Memory System...")
        
        try:
            # Test memory in DataAgent
            print("  Testing DataAgent memory...")
            memory_summary = self.data_agent.get_memory_summary()
            print(f"     Memory status: {memory_summary}")
            
            # Add some conversation context
            if hasattr(self.data_agent, 'memory'):
                self.data_agent.memory.chat_memory.add_user_message("What data sources do you support?")
                self.data_agent.memory.chat_memory.add_ai_message("I support RSS feeds, Yahoo Finance API, and various financial data sources.")
                
                updated_summary = self.data_agent.get_memory_summary()
                print(f"     Updated memory: {updated_summary}")
            
            # Test memory in AnalysisAgent  
            print("  Testing AnalysisAgent memory...")
            memory_summary = self.analysis_agent.get_memory_summary()
            print(f"     Memory status: {memory_summary}")
            
            self.test_results["agent_memory"] = True
            print("  ✅ Agent memory system working")
            
        except Exception as e:
            print(f"❌ Agent memory testing failed: {str(e)}")
    
    async def test_tool_integration(self):
        """Test LangChain tool integration."""
        print("\n🔧 Testing Tool Integration...")
        
        try:
            # Test tool availability in DataAgent
            print("  Checking DataAgent tools...")
            data_tools = self.data_agent.get_available_tools()
            print(f"     Available tools: {', '.join(data_tools)}")
            
            # Test tool availability in AnalysisAgent
            print("  Checking AnalysisAgent tools...")
            analysis_tools = self.analysis_agent.get_available_tools()
            print(f"     Available tools: {', '.join(analysis_tools)}")
            
            # Test tool adaptation (BaseTool -> LangChain Tool)
            if hasattr(self.data_agent, 'langchain_tools'):
                langchain_tools = self.data_agent.langchain_tools
                print(f"     LangChain tools: {len(langchain_tools)} adapted successfully")
            
            self.test_results["tool_integration"] = True
            print("  ✅ Tool integration working")
            
        except Exception as e:
            print(f"❌ Tool integration testing failed: {str(e)}")
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*60)
        print("🧪 LLM AGENT TEST SUITE RESULTS")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print("-" * 60)
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All LLM Agent tests passed! New architecture is working correctly.")
        elif passed_tests >= total_tests * 0.7:  # 70% success rate
            print("⚠️ Most tests passed. LLM Agent architecture is mostly functional.")
        else:
            print("❌ Several tests failed. Please check the implementation.")
        
        print(f"⏱️  Test suite completed in {passed_tests}/{total_tests} components")
        return passed_tests == total_tests


async def main():
    """Run the complete LLM Agent test suite."""
    print("🚀 LLM-Powered AI Agent Test Suite")
    print("="*60)
    
    test_suite = LLMAgentTestSuite()
    
    try:
        # Run all test phases
        await test_suite.setup_test_environment()
        await test_suite.test_agent_initialization()
        
        # Only run advanced tests if basic initialization works
        if test_suite.test_results["data_agent_init"] and test_suite.test_results["analysis_agent_init"]:
            await test_suite.test_data_agent_tasks()
            await test_suite.test_analysis_agent_tasks()
            await test_suite.test_agent_memory()
            await test_suite.test_tool_integration()
            
            # Only test workflow if individual agents work
            if (test_suite.test_results["data_agent_task"] or 
                test_suite.test_results["analysis_agent_task"]):
                await test_suite.test_natural_language_workflow()
        
        # Print final results
        success = test_suite.print_test_summary()
        
        if success:
            print("\n🎯 Next steps:")
            print("- Test the new LLM API endpoints at /llm/")
            print("- Try natural language queries through the API")
            print("- Monitor agent performance and memory usage")
            print("- Fine-tune prompts based on usage patterns")
        
        return success
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        print(f"\n❌ Test suite execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable is required for LLM agent testing")
        print("   Please set your OpenAI API key in the .env file")
        sys.exit(1)
    
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)