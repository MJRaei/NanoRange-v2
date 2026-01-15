"""
ADK-compatible agent module.

This module exposes the root_agent for use with ADK CLI commands:
- adk run nanorange
- adk web

The NanoRange system uses a multi-agent architecture:
- Root Coordinator: Routes requests between sub-agents
- Pipeline Planner: Analyzes requests and designs pipelines
- Pipeline Executor: Builds and runs pipelines
"""

from nanorange.storage.database import init_database
from nanorange.core.registry import get_registry
from nanorange.agent.orchestrator import create_orchestrator_agent

# Initialize system on import
init_database()

# Discover and register built-in tools
registry = get_registry()
registry.discover_tools()

# Create the root agent for ADK (multi-agent system)
root_agent = create_orchestrator_agent(mode="full")

# Also expose individual agents for testing
planner_agent = create_orchestrator_agent(mode="planner")
executor_agent = create_orchestrator_agent(mode="executor")
