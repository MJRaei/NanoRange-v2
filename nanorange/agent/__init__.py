"""
Agent components for NanoRange orchestration.

Multi-agent architecture:
- Root Coordinator: Routes between sub-agents
- Pipeline Planner: Analyzes requests and designs pipelines  
- Pipeline Executor: Builds and runs pipelines
"""

from nanorange.agent.orchestrator import (
    NanoRangeOrchestrator,
    create_orchestrator_agent,
)
from nanorange.agent.agents import (
    create_root_agent,
    create_planner_agent,
    create_executor_agent,
    create_standalone_planner,
    create_standalone_executor,
)
from nanorange.agent.meta_tools import (
    list_available_tools,
    create_step,
    connect_steps,
    set_parameter,
    validate_pipeline,
    execute_pipeline,
    get_results,
    modify_step,
    remove_step,
    save_pipeline,
    load_pipeline,
    get_pipeline_summary,
)
from nanorange.agent.planner_tools import (
    list_tools_for_planning,
    create_pipeline_plan,
    analyze_image_for_planning,
    get_tool_compatibility,
)

__all__ = [
    # Orchestrator
    "NanoRangeOrchestrator",
    "create_orchestrator_agent",
    # Agent creation
    "create_root_agent",
    "create_planner_agent",
    "create_executor_agent",
    "create_standalone_planner",
    "create_standalone_executor",
    # Meta tools (executor)
    "list_available_tools",
    "create_step",
    "connect_steps",
    "set_parameter",
    "validate_pipeline",
    "execute_pipeline",
    "get_results",
    "modify_step",
    "remove_step",
    "save_pipeline",
    "load_pipeline",
    "get_pipeline_summary",
    # Planner tools
    "list_tools_for_planning",
    "create_pipeline_plan",
    "analyze_image_for_planning",
    "get_tool_compatibility",
]
