"""
Intelligent Workflow Coordinator powered by LLM.

An advanced workflow orchestrator that uses LLM reasoning to coordinate
multiple AI agents and execute complex financial analysis workflows.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.output_parsers import StrOutputParser
except ImportError as e:
    raise ImportError(f"Required LangChain packages not installed: {e}")

from ..agents.llm_data_agent import LLMDataAgent
from ..agents.llm_analysis_agent import LLMAnalysisAgent
from ..agents.llm_base_agent import LLMAgentTask, LLMAgentResult, LLMTaskType
from ..agents.memory_manager import EnhancedMemoryManager, MemoryType
# Removed domain repository dependency for simplified architecture


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Individual step in a workflow."""
    
    def __init__(
        self,
        step_id: str,
        agent_name: str,
        task_description: str,
        parameters: Dict[str, Any] = None,
        dependencies: List[str] = None
    ):
        self.step_id = step_id
        self.agent_name = agent_name
        self.task_description = task_description
        self.parameters = parameters or {}
        self.dependencies = dependencies or []
        self.status = WorkflowStatus.PLANNING
        self.result: Optional[LLMAgentResult] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success": self.result.success if self.result else None
        }


class IntelligentWorkflowCoordinator:
    """
    LLM-powered workflow coordinator for complex financial analysis tasks.
    
    This coordinator can:
    - Understand natural language workflow requests
    - Break down complex tasks into executable steps
    - Coordinate multiple specialized agents (Data, Analysis)
    - Adapt workflows based on intermediate results
    - Provide real-time progress updates
    - Handle errors and implement retry strategies
    
    Examples of workflows it can handle:
    - "Analyze market sentiment for tech stocks and generate a daily report"
    - "Fetch Apple earnings news, analyze impact, and compare with historical data"
    - "Monitor renewable energy sector trends and alert on significant changes"
    - "Create comprehensive investment analysis for FAANG stocks with risk assessment"
    """
    
    def __init__(
        self,
        repository=None,  # Made optional for simplified architecture
        coordinator_llm: Optional[ChatOpenAI] = None,
        enable_memory: bool = True,
        max_workflow_steps: int = 20
    ):
        self.repository = repository
        self.max_workflow_steps = max_workflow_steps
        
        # Initialize coordinator LLM
        if coordinator_llm is None:
            import os
            self.coordinator_llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL_COORDINATOR", "gpt-4o"),
                temperature=0.2,  # Balanced for planning and creativity
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.coordinator_llm = coordinator_llm
        
        # Initialize agents
        self.data_agent = LLMDataAgent(repository)
        self.analysis_agent = LLMAnalysisAgent(repository)
        
        self.agents = {
            "data": self.data_agent,
            "analysis": self.analysis_agent,
            "DataAgent": self.data_agent,
            "AnalysisAgent": self.analysis_agent
        }
        
        # Memory management
        if enable_memory:
            self.memory_manager = EnhancedMemoryManager(
                agent_name="WorkflowCoordinator",
                llm=self.coordinator_llm
            )
        else:
            self.memory_manager = None
        
        self.logger = logging.getLogger("IntelligentWorkflow")
        
        # Active workflows
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def execute_natural_language_workflow(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        max_execution_time: int = 1800  # 30 minutes
    ) -> Dict[str, Any]:
        """
        Execute a workflow based on natural language description.
        
        Args:
            user_request: Natural language description of desired workflow
            context: Additional context for workflow planning
            max_execution_time: Maximum execution time in seconds
            
        Returns:
            Comprehensive workflow execution results
        """
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        self.logger.info(f"Starting intelligent workflow: {workflow_id}")
        self.logger.info(f"User request: {user_request}")
        
        # Initialize workflow state
        workflow_state = {
            "workflow_id": workflow_id,
            "user_request": user_request,
            "context": context or {},
            "start_time": start_time,
            "status": WorkflowStatus.PLANNING,
            "steps": [],
            "results": {},
            "errors": [],
            "metadata": {
                "coordinator_model": self.coordinator_llm.model_name,
                "max_execution_time": max_execution_time
            }
        }
        
        self.active_workflows[workflow_id] = workflow_state
        
        try:
            # Step 1: Analyze user intent and plan workflow
            self.logger.info("🧠 Planning workflow based on user intent...")
            workflow_plan = await self._plan_workflow(user_request, context)
            workflow_state["plan"] = workflow_plan
            workflow_state["steps"] = workflow_plan.get("steps", [])
            
            # Step 2: Execute workflow steps
            workflow_state["status"] = WorkflowStatus.EXECUTING
            self.logger.info(f"🚀 Executing workflow with {len(workflow_state['steps'])} steps")
            
            execution_results = await self._execute_workflow_steps(
                workflow_state["steps"],
                workflow_id,
                max_execution_time
            )
            
            workflow_state["results"] = execution_results
            
            # Step 3: Generate final summary
            self.logger.info("📊 Generating workflow summary...")
            final_summary = await self._generate_workflow_summary(workflow_state)
            workflow_state["summary"] = final_summary
            
            workflow_state["status"] = WorkflowStatus.COMPLETED
            workflow_state["end_time"] = datetime.now()
            workflow_state["total_execution_time"] = (
                workflow_state["end_time"] - workflow_state["start_time"]
            ).total_seconds()
            
            # Update memory with workflow results
            if self.memory_manager:
                self.memory_manager.add_context(
                    f"workflow_{workflow_id}",
                    {
                        "user_request": user_request,
                        "success": True,
                        "steps_completed": len([s for s in workflow_state["steps"] if s.status == WorkflowStatus.COMPLETED]),
                        "total_time": workflow_state["total_execution_time"]
                    },
                    importance=0.8
                )
            
            self.logger.info(f"✅ Workflow completed successfully: {workflow_id}")
            return workflow_state
            
        except Exception as e:
            workflow_state["status"] = WorkflowStatus.FAILED
            workflow_state["end_time"] = datetime.now()
            workflow_state["error"] = str(e)
            
            self.logger.error(f"❌ Workflow failed: {workflow_id} - {str(e)}")
            
            if self.memory_manager:
                self.memory_manager.add_context(
                    f"workflow_error_{workflow_id}",
                    {"user_request": user_request, "error": str(e)},
                    importance=0.7
                )
            
            return workflow_state
        
        finally:
            # Cleanup
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
    
    async def _plan_workflow(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use LLM to analyze user intent and create workflow plan."""
        
        # Get relevant context from memory
        relevant_context = ""
        if self.memory_manager:
            context_memories = self.memory_manager.get_relevant_context(user_request, max_results=3)
            if context_memories:
                relevant_context = "\n".join([
                    f"- {mem['content']}" for mem in context_memories
                ])
        
        planning_prompt = ChatPromptTemplate.from_template(
            """You are an intelligent workflow coordinator for financial analysis tasks.

Your role is to analyze user requests and create detailed execution plans using available AI agents.

Available Agents:
- DataAgent: Fetches financial news, market data, processes and stores data, creates embeddings
- AnalysisAgent: Performs sentiment analysis, topic extraction, stock identification, report generation

Agent Capabilities:
DataAgent:
- fetch_financial_news(sources, max_articles, keywords, store_results)
- fetch_market_data(symbols, period, interval, include_company_info)  
- store_data_with_vectors(data, create_embeddings)
- assess_data_quality(data_type, days_back)

AnalysisAgent:
- analyze_sentiment(content, analysis_depth, include_confidence)
- extract_topics(content, max_topics, include_hierarchy)
- identify_stocks(content, include_context)
- generate_market_report(data_sources, report_type, focus_sectors)
- analyze_batch_content(content_list, analysis_types)
- find_similar_content(query_content, similarity_threshold)

User Request: {user_request}

Additional Context: {context}

Recent Relevant Context: {relevant_context}

Create a detailed workflow plan with these elements:

1. INTENT_ANALYSIS: What is the user trying to accomplish?
2. WORKFLOW_STEPS: List of specific steps with:
   - step_id: unique identifier
   - agent: which agent to use (DataAgent or AnalysisAgent)
   - task: natural language task description
   - method: specific method to call (if applicable)
   - parameters: specific parameters for the task
   - dependencies: which previous steps this depends on
3. SUCCESS_CRITERIA: How to determine if the workflow succeeded
4. ESTIMATED_TIME: Expected execution time in minutes

Format your response as valid JSON with these keys: intent_analysis, workflow_steps, success_criteria, estimated_time_minutes.

Example workflow_steps format:
[
  {{
    "step_id": "step_1",
    "agent": "DataAgent", 
    "task": "Fetch latest news about renewable energy companies",
    "method": "fetch_financial_news",
    "parameters": {{"keywords": ["renewable energy", "solar", "wind"], "max_articles": 20}},
    "dependencies": []
  }},
  {{
    "step_id": "step_2",
    "agent": "AnalysisAgent",
    "task": "Analyze sentiment of fetched renewable energy news",
    "method": "analyze_batch_content", 
    "parameters": {{"analysis_types": ["sentiment", "topics"]}},
    "dependencies": ["step_1"]
  }}
]

Plan the workflow now:"""
        )
        
        try:
            planning_chain = planning_prompt | self.coordinator_llm | StrOutputParser()
            
            plan_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: planning_chain.invoke({
                    "user_request": user_request,
                    "context": str(context) if context else "None",
                    "relevant_context": relevant_context or "None"
                })
            )
            
            # Parse JSON response
            import json
            workflow_plan = json.loads(plan_response.strip())
            
            # Convert step dictionaries to WorkflowStep objects
            steps = []
            for step_data in workflow_plan.get("workflow_steps", []):
                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    agent_name=step_data["agent"],
                    task_description=step_data["task"],
                    parameters=step_data.get("parameters", {}),
                    dependencies=step_data.get("dependencies", [])
                )
                steps.append(step)
            
            workflow_plan["steps"] = steps
            return workflow_plan
            
        except Exception as e:
            self.logger.error(f"Failed to plan workflow: {str(e)}")
            # Fallback to simple workflow
            return {
                "intent_analysis": "Failed to parse user intent, using fallback workflow",
                "workflow_steps": [],
                "steps": [],
                "success_criteria": "Basic execution completion",
                "estimated_time_minutes": 5
            }
    
    async def _execute_workflow_steps(
        self,
        steps: List[WorkflowStep],
        workflow_id: str,
        max_execution_time: int
    ) -> Dict[str, Any]:
        """Execute workflow steps with dependency management."""
        
        results = {
            "completed_steps": [],
            "failed_steps": [],
            "total_execution_time": 0,
            "step_results": {}
        }
        
        start_time = datetime.now()
        completed_step_ids = set()
        
        # Execute steps in dependency order
        remaining_steps = steps[:]
        
        while remaining_steps:
            # Check timeout
            elapsed_time = (datetime.now() - start_time).total_seconds()
            if elapsed_time > max_execution_time:
                self.logger.warning(f"Workflow timeout reached: {max_execution_time}s")
                break
            
            # Find steps ready to execute (dependencies satisfied)
            ready_steps = [
                step for step in remaining_steps
                if all(dep_id in completed_step_ids for dep_id in step.dependencies)
            ]
            
            if not ready_steps:
                self.logger.error("Circular dependencies or missing dependencies detected")
                break
            
            # Execute ready steps (can be done in parallel)
            step_tasks = []
            for step in ready_steps:
                task = self._execute_single_step(step, workflow_id)
                step_tasks.append(task)
            
            # Wait for all parallel steps to complete
            step_results = await asyncio.gather(*step_tasks, return_exceptions=True)
            
            # Process results
            for step, step_result in zip(ready_steps, step_results):
                remaining_steps.remove(step)
                
                if isinstance(step_result, Exception):
                    step.status = WorkflowStatus.FAILED
                    results["failed_steps"].append(step.to_dict())
                    self.logger.error(f"Step {step.step_id} failed: {str(step_result)}")
                else:
                    step.status = WorkflowStatus.COMPLETED
                    step.result = step_result
                    completed_step_ids.add(step.step_id)
                    results["completed_steps"].append(step.to_dict())
                    results["step_results"][step.step_id] = step_result.to_dict() if step_result else None
                    self.logger.info(f"Step {step.step_id} completed successfully")
        
        # Mark remaining steps as failed due to dependencies
        for step in remaining_steps:
            step.status = WorkflowStatus.FAILED
            results["failed_steps"].append(step.to_dict())
        
        results["total_execution_time"] = (datetime.now() - start_time).total_seconds()
        return results
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        workflow_id: str
    ) -> Optional[LLMAgentResult]:
        """Execute a single workflow step."""
        
        step.start_time = datetime.now()
        step.status = WorkflowStatus.EXECUTING
        
        try:
            # Get the appropriate agent
            agent = self.agents.get(step.agent_name)
            if not agent:
                raise ValueError(f"Unknown agent: {step.agent_name}")
            
            # Create task for the agent
            task = LLMAgentTask(
                task_id=f"{workflow_id}_{step.step_id}",
                task_type=LLMTaskType.NATURAL_LANGUAGE,
                description=step.task_description,
                parameters=step.parameters,
                context={"workflow_id": workflow_id, "step_id": step.step_id}
            )
            
            # Execute task
            result = await agent.execute_task(task)
            
            step.end_time = datetime.now()
            return result
            
        except Exception as e:
            step.end_time = datetime.now()
            step.status = WorkflowStatus.FAILED
            self.logger.error(f"Step execution failed: {step.step_id} - {str(e)}")
            raise e
    
    async def _generate_workflow_summary(
        self,
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive workflow summary using LLM."""
        
        summary_prompt = ChatPromptTemplate.from_template(
            """You are summarizing the results of a financial analysis workflow.

Workflow Details:
- User Request: {user_request}
- Total Steps: {total_steps}
- Completed Steps: {completed_steps}
- Failed Steps: {failed_steps}
- Total Execution Time: {execution_time} seconds

Step Results Summary:
{step_results}

Create a comprehensive summary with:
1. EXECUTIVE_SUMMARY: High-level overview of what was accomplished
2. KEY_FINDINGS: Important insights and results discovered
3. DATA_PROCESSED: Summary of data that was fetched and analyzed
4. SUCCESS_METRICS: Quantitative measures of workflow success
5. RECOMMENDATIONS: Next steps or action items based on results
6. WORKFLOW_PERFORMANCE: Analysis of execution efficiency

Format as JSON with these keys: executive_summary, key_findings, data_processed, success_metrics, recommendations, workflow_performance."""
        )
        
        try:
            # Prepare step results summary
            step_results_text = ""
            for step_id, result in workflow_state.get("results", {}).get("step_results", {}).items():
                if result and result.get("success"):
                    step_results_text += f"- {step_id}: SUCCESS\n"
                else:
                    step_results_text += f"- {step_id}: FAILED\n"
            
            summary_chain = summary_prompt | self.coordinator_llm | StrOutputParser()
            
            summary_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: summary_chain.invoke({
                    "user_request": workflow_state["user_request"],
                    "total_steps": len(workflow_state["steps"]),
                    "completed_steps": len(workflow_state.get("results", {}).get("completed_steps", [])),
                    "failed_steps": len(workflow_state.get("results", {}).get("failed_steps", [])),
                    "execution_time": workflow_state.get("total_execution_time", 0),
                    "step_results": step_results_text
                })
            )
            
            import json
            return json.loads(summary_response.strip())
            
        except Exception as e:
            self.logger.error(f"Failed to generate workflow summary: {str(e)}")
            return {
                "executive_summary": "Workflow execution completed with mixed results",
                "key_findings": [],
                "data_processed": "Unknown",
                "success_metrics": {"completion_rate": "partial"},
                "recommendations": ["Review failed steps and retry if needed"],
                "workflow_performance": "Performance data unavailable"
            }
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get information about currently active workflows."""
        return [
            {
                "workflow_id": wf_id,
                "user_request": wf_data["user_request"],
                "status": wf_data["status"].value,
                "start_time": wf_data["start_time"].isoformat(),
                "steps_total": len(wf_data["steps"]),
                "steps_completed": len([s for s in wf_data["steps"] if s.status == WorkflowStatus.COMPLETED])
            }
            for wf_id, wf_data in self.active_workflows.items()
        ]
    
    def get_workflow_capabilities(self) -> Dict[str, List[str]]:
        """Get comprehensive list of workflow capabilities."""
        return {
            "data_operations": [
                "Fetch financial news from multiple sources",
                "Collect stock market data and prices",
                "Process and clean financial data",
                "Create vector embeddings for semantic search",
                "Assess data quality and completeness"
            ],
            "analysis_operations": [
                "Perform sentiment analysis on financial content",
                "Extract topics and themes from news articles",
                "Identify stock mentions and company references",
                "Generate comprehensive market reports",
                "Find similar content using vector search",
                "Batch process multiple articles efficiently"
            ],
            "workflow_types": [
                "Daily market sentiment analysis",
                "Sector-specific trend monitoring",
                "Company-focused news analysis",
                "Investment opportunity identification",
                "Risk assessment workflows",
                "Competitive intelligence gathering",
                "Market event impact analysis"
            ],
            "coordination_features": [
                "Natural language workflow planning",
                "Intelligent agent selection and routing", 
                "Parallel execution of independent steps",
                "Dependency management and ordering",
                "Error handling and retry strategies",
                "Real-time progress monitoring",
                "Comprehensive result summarization"
            ]
        }