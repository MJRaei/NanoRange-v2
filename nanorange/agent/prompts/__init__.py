"""
System prompts for NanoRange agents.

Contains specialized prompts for:
- Coordinator: Routing between planner and executor agents
- Pipeline Planner: Designing analysis pipelines
- Pipeline Executor: Building and running pipelines
"""

from nanorange.agent.prompts.coordinator_prompts import (
    COORDINATOR_SYSTEM_PROMPT,
    get_coordinator_prompt,
)
from nanorange.agent.prompts.planner_prompts import (
    PLANNER_SYSTEM_PROMPT,
    get_planner_prompt,
)
from nanorange.agent.prompts.executor_prompts import (
    EXECUTOR_SYSTEM_PROMPT,
    PIPELINE_BUILDING_PROMPT,
    ERROR_HANDLING_PROMPT,
    RESULT_EXPLANATION_PROMPT,
    EXAMPLE_EXECUTION_PROMPT,
    get_executor_prompt,
)

__all__ = [
    # Coordinator
    "COORDINATOR_SYSTEM_PROMPT",
    "get_coordinator_prompt",
    # Planner
    "PLANNER_SYSTEM_PROMPT",
    "get_planner_prompt",
    # Executor
    "EXECUTOR_SYSTEM_PROMPT",
    "PIPELINE_BUILDING_PROMPT",
    "ERROR_HANDLING_PROMPT",
    "RESULT_EXPLANATION_PROMPT",
    "EXAMPLE_EXECUTION_PROMPT",
    "get_executor_prompt",
]
