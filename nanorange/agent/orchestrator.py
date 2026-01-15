"""
NanoRange Orchestrator - High-level interface for the multi-agent system.

Provides:
- NanoRangeOrchestrator class for programmatic interaction
- CLI-friendly chat interface
- ADK-compatible agent creation
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from nanorange.agent.agents import (
    create_root_agent,
    create_planner_agent,
    create_executor_agent,
    create_standalone_planner,
    create_standalone_executor,
)
from nanorange.agent.meta_tools import initialize_session


class NanoRangeOrchestrator:
    """
    High-level wrapper for the NanoRange multi-agent system.
    
    Provides a simple interface for interacting with the agent team:
    - Planner Agent: Designs pipelines from user requests
    - Executor Agent: Builds and runs pipelines
    
    The root coordinator routes requests to the appropriate agent.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        session_id: Optional[str] = None,
        mode: str = "full"  # "full", "planner", "executor"
    ):
        """
        Initialize the orchestrator.
        
        Args:
            model: Gemini model to use
            session_id: Optional existing session to resume
            mode: Agent mode:
                - "full": Root agent with planner and executor sub-agents
                - "planner": Standalone planner only
                - "executor": Standalone executor only
        """
        self.model = model
        self.mode = mode
        self.nano_session_id = initialize_session(session_id)
        
        # Create appropriate agent based on mode
        if mode == "planner":
            self.agent = create_standalone_planner(model)
        elif mode == "executor":
            self.agent = create_standalone_executor(model)
        else:
            self.agent = create_root_agent(model)
        
        self.app_name = "nanorange"
        self.user_id = "nanorange_user"
        self.adk_session_id = str(uuid4())
        
        # Create runner
        self.runner = InMemoryRunner(agent=self.agent, app_name=self.app_name)
        self._session_created = False
    
    async def _ensure_session(self):
        """Ensure ADK session is created."""
        if not self._session_created:
            await self.runner.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.adk_session_id,
            )
            self._session_created = True
    
    async def chat(self, message: str) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: User message
            
        Returns:
            Agent response text
        """
        await self._ensure_session()
        
        content = types.Content(
            role="user",
            parts=[types.Part(text=message)]
        )
        
        response_text = ""
        
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.adk_session_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
        
        return response_text.strip() if response_text else "I processed your request."
    
    async def chat_with_image(self, message: str, image_path: str) -> str:
        """
        Send a message with an image attachment.
        
        Args:
            message: User message
            image_path: Path to image file
            
        Returns:
            Agent response text
        """
        from pathlib import Path
        from PIL import Image
        import base64
        import io
        
        await self._ensure_session()
        
        # Load and encode image
        img_path = Path(image_path)
        if not img_path.exists():
            return f"Error: Image not found at {image_path}"
        
        # Read image and convert to base64
        with Image.open(img_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            image_bytes = buffer.getvalue()
        
        # Create content with image
        content = types.Content(
            role="user",
            parts=[
                types.Part(text=message),
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=image_bytes
                    )
                ),
            ]
        )
        
        response_text = ""
        
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.adk_session_id,
            new_message=content,
        ):
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
    
    def get_mode(self) -> str:
        """Get the current agent mode."""
        return self.mode


def create_orchestrator_agent(
    model: str = "gemini-2.0-flash",
    mode: str = "full"
) -> Agent:
    """
    Create a NanoRange agent for ADK CLI/web interface.
    
    Args:
        model: Gemini model to use
        mode: "full", "planner", or "executor"
        
    Returns:
        Configured ADK Agent
    """
    initialize_session()
    
    if mode == "planner":
        return create_standalone_planner(model)
    elif mode == "executor":
        return create_standalone_executor(model)
    else:
        return create_root_agent(model)


# Default agent for ADK CLI - uses the full multi-agent system
root_agent = create_orchestrator_agent(mode="full")
