"""
NanoRange Multi-Agent System.

Defines the agent hierarchy:
- Root Agent: Coordinates between sub-agents
- Planner Agent: Analyzes requests and designs pipelines
- Executor Agent: Builds and runs pipelines

Uses Google ADK's multi-agent capabilities for agent delegation.
"""

from typing import Optional
from google.adk.agents import Agent

from nanorange.agent.prompts import (
    get_coordinator_prompt,
    get_planner_prompt,
    get_executor_prompt,
)
from nanorange.agent.planner_tools import (
    list_tools_for_planning,
    create_pipeline_plan,
    analyze_image_for_planning,
    get_tool_compatibility,
)
from nanorange.agent.meta_tools import (
    # Pipeline building tools
    new_pipeline,
    create_step,
    connect_steps,
    set_parameter,
    modify_step,
    remove_step,
    # Validation & execution
    validate_pipeline,
    execute_pipeline,
    get_results,
    get_pipeline_summary,
    # Persistence
    save_pipeline,
    load_pipeline,
    list_saved_pipelines,
    export_pipeline,
    import_pipeline,
    # Session
    initialize_session,
)


def create_planner_agent(model: str = "gemini-2.0-flash") -> Agent:
    """
    Create the Pipeline Planner Agent.
    
    The planner analyzes user requests and images to design
    optimal analysis pipelines. It presents plans for approval
    before execution.
    
    Args:
        model: Gemini model to use
        
    Returns:
        Configured Planner Agent
    """
    return Agent(
        model=model,
        name="pipeline_planner",
        description=(
            "Expert at analyzing microscopy images and user requests to design "
            "optimal image analysis pipelines. Reviews images, discovers available "
            "tools, and creates step-by-step plans for user approval."
        ),
        instruction=get_planner_prompt(),
        tools=[
            list_tools_for_planning,
            create_pipeline_plan,
            analyze_image_for_planning,
            get_tool_compatibility,
        ],
    )


def create_executor_agent(model: str = "gemini-2.0-flash") -> Agent:
    """
    Create the Pipeline Executor Agent.
    
    The executor builds and runs approved pipelines using
    all available analysis tools.
    
    Args:
        model: Gemini model to use
        
    Returns:
        Configured Executor Agent
    """
    return Agent(
        model=model,
        name="pipeline_executor",
        description=(
            "Expert at building and executing image analysis pipelines. "
            "Takes approved plans from the Planner and executes them, "
            "handling errors and reporting results."
        ),
        instruction=get_executor_prompt(),
        tools=[
            # Pipeline building
            new_pipeline,
            create_step,
            connect_steps,
            set_parameter,
            modify_step,
            remove_step,
            # Validation & execution
            validate_pipeline,
            execute_pipeline,
            get_results,
            get_pipeline_summary,
            # Persistence
            save_pipeline,
            load_pipeline,
            list_saved_pipelines,
            export_pipeline,
            import_pipeline,
        ],
    )


def create_root_agent(model: str = "gemini-2.0-flash") -> Agent:
    """
    Create the Root Coordinator Agent.
    
    The root agent coordinates between the Planner and Executor,
    routing requests to the appropriate sub-agent.
    
    Args:
        model: Gemini model to use
        
    Returns:
        Configured Root Agent with sub-agents
    """
    initialize_session()
    
    planner = create_planner_agent(model)
    executor = create_executor_agent(model)
    
    return Agent(
        model=model,
        name="nanorange_coordinator",
        description=(
            "NanoRange Coordinator - Routes requests between the Pipeline Planner "
            "(for analyzing images and designing pipelines) and Pipeline Executor "
            "(for running pipelines and managing results)."
        ),
        instruction=get_coordinator_prompt(),
        sub_agents=[planner, executor],
    )


def create_standalone_planner(model: str = "gemini-2.0-flash") -> Agent:
    """
    Create a standalone Planner Agent (without root coordinator).
    
    Useful for testing or when only planning functionality is needed.
    """
    initialize_session()
    return create_planner_agent(model)


def create_standalone_executor(model: str = "gemini-2.0-flash") -> Agent:
    """
    Create a standalone Executor Agent (without root coordinator).
    
    Useful for testing or when only execution functionality is needed.
    """
    initialize_session()
    return create_executor_agent(model)
