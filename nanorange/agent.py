"""
ADK-compatible agent module.

This module exposes the root_agent for use with ADK CLI commands:
- adk run nanorange
- adk web
"""

from nanorange.storage.database import init_database
from nanorange.core.registry import get_registry
from nanorange.agent.orchestrator import create_orchestrator

# Initialize system on import
init_database()

# Discover and register built-in tools
registry = get_registry()
registry.discover_tools()

# Create the root agent for ADK
root_agent = create_orchestrator()
