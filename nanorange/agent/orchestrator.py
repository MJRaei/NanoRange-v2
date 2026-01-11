"""
NanoRange Orchestrator Agent - Main ADK agent for pipeline orchestration.

This agent uses Google ADK with Gemini to:
- Understand user requests for image analysis
- Plan and build analysis pipelines
- Execute and iterate on results
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from nanorange.agent.prompts import get_full_system_prompt
from nanorange.agent.meta_tools import (
    list_available_tools,
    get_tool_details,
    new_pipeline,
    create_step,
    connect_steps,
    set_parameter,
    modify_step,
    remove_step,
    validate_pipeline,
    execute_pipeline,
    get_results,
    get_pipeline_summary,
    save_pipeline,
    load_pipeline,
    list_saved_pipelines,
    export_pipeline,
    import_pipeline,
    initialize_session,
)


def create_agent(model: str = "gemini-2.0-flash") -> Agent:
    """Create the NanoRange orchestrator agent."""
    return Agent(
        model=model,
        name="nanorange_orchestrator",
        description=(
            "Expert AI assistant for microscopy image analysis. "
            "Builds and executes image analysis pipelines by connecting "
            "specialized tools."
        ),
        instruction=get_full_system_prompt(),
        tools=[
            # Tool discovery
            list_available_tools,
            get_tool_details,
            
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


class NanoRangeOrchestrator:
    """
    High-level wrapper for the NanoRange orchestrator agent.
    
    Provides initialization, configuration, and session management.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        session_id: Optional[str] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            model: Gemini model to use
            session_id: Optional existing session to resume
        """
        self.model = model
        self.nano_session_id = initialize_session(session_id)
        self.agent = create_agent(model)
        self.app_name = "nanorange"
        self.user_id = "nanorange_user"
        self.adk_session_id = str(uuid4())
        
        # Create runner
        self.runner = InMemoryRunner(agent=self.agent, app_name=self.app_name)
        
        # Create the ADK session synchronously
        self._session_created = False
    
    async def _ensure_session(self):
        """Ensure ADK session is created."""
        if not self._session_created:
            # Create session in the runner's session service
            await self.runner.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.adk_session_id,
            )
            self._session_created = True
    
    async def chat(self, message: str) -> str:
        """
        Send a message to the orchestrator and get a response.
        
        Args:
            message: User message
            
        Returns:
            Agent response text
        """
        # Ensure session exists
        await self._ensure_session()
        
        # Create content from user message
        content = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
        
        # Collect response text from events
        response_text = ""
        
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.adk_session_id,
            new_message=content,
        ):
            # Extract text from model responses
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
        
        return response_text.strip() if response_text else "I processed your request."
    
    async def close(self):
        """Clean up resources."""
        await self.runner.close()
    
    def get_session_id(self) -> str:
        """Get the current NanoRange session ID."""
        return self.nano_session_id


def create_orchestrator(
    model: str = "gemini-2.0-flash",
    session_id: Optional[str] = None
) -> Agent:
    """
    Create a NanoRange orchestrator agent.
    
    This is the main entry point for creating an agent that can be used
    with ADK's run command or web interface.
    
    Args:
        model: Gemini model to use (default: gemini-2.0-flash)
        session_id: Optional existing session to resume
        
    Returns:
        Configured ADK Agent
    """
    # Initialize NanoRange session
    initialize_session(session_id)
    
    # Create and return the agent
    return create_agent(model)


# Default agent instance for ADK CLI
# This is discovered by `adk run nanorange`
root_agent = create_orchestrator()
