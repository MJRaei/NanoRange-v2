"""
Base classes for NanoRange tools.

Tools can be implemented as either:
1. Function tools - Simple functions decorated with @tool
2. Class-based tools - Classes inheriting from ToolBase
3. Agent tools - Sub-agents that act as tools
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from nanorange.core.schemas import (
    DataType,
    InputSchema,
    OutputSchema,
    ToolSchema,
    ToolType,
)


class ToolBase(ABC):
    """
    Abstract base class for class-based tools.
    
    Subclasses must:
    1. Define class attributes for schema information
    2. Implement the execute() method
    
    Example:
        class GaussianBlurTool(ToolBase):
            tool_id = "gaussian_blur"
            name = "Gaussian Blur"
            description = "Applies Gaussian blur to an image"
            category = "preprocessing"
            
            inputs = [
                InputSchema(name="image_path", type=DataType.IMAGE, required=True),
                InputSchema(name="sigma", type=DataType.FLOAT, default=1.0),
            ]
            outputs = [
                OutputSchema(name="blurred_image", type=DataType.IMAGE),
            ]
            
            def execute(self, image_path: str, sigma: float = 1.0) -> Dict[str, Any]:
                # Implementation
                return {"blurred_image": output_path}
    """
    
    # Required class attributes
    tool_id: str
    name: str
    description: str
    
    # Optional class attributes
    category: str = "general"
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: List[str] = []
    
    # Input/output definitions
    inputs: List[InputSchema] = []
    outputs: List[OutputSchema] = []
    
    def __init__(self, **kwargs):
        """Initialize the tool with optional configuration."""
        self.config = kwargs
    
    @abstractmethod
    def execute(self, **inputs) -> Dict[str, Any]:
        """
        Execute the tool with the given inputs.
        
        Args:
            **inputs: Input values matching the input schema
            
        Returns:
            Dictionary mapping output names to values
        """
        pass
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Generate the tool schema from class attributes."""
        return ToolSchema(
            tool_id=cls.tool_id,
            name=cls.name,
            description=cls.description,
            type=ToolType.FUNCTION,
            category=cls.category,
            inputs=cls.inputs,
            outputs=cls.outputs,
            version=cls.version,
            author=cls.author,
            tags=cls.tags,
        )
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate inputs against the schema.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        schema = self.get_schema()
        
        for inp in schema.inputs:
            if inp.name not in inputs:
                if inp.required:
                    errors.append(f"Missing required input: {inp.name}")
            else:
                value = inputs[inp.name]
                # Type validation could be more sophisticated
                if inp.type == DataType.FLOAT and not isinstance(value, (int, float)):
                    errors.append(f"Input '{inp.name}' must be a number")
                elif inp.type == DataType.INT and not isinstance(value, int):
                    errors.append(f"Input '{inp.name}' must be an integer")
                elif inp.type == DataType.STRING and not isinstance(value, str):
                    errors.append(f"Input '{inp.name}' must be a string")
                elif inp.type == DataType.BOOL and not isinstance(value, bool):
                    errors.append(f"Input '{inp.name}' must be a boolean")
                
                # Range validation
                if inp.min_value is not None and isinstance(value, (int, float)):
                    if value < inp.min_value:
                        errors.append(
                            f"Input '{inp.name}' must be >= {inp.min_value}"
                        )
                if inp.max_value is not None and isinstance(value, (int, float)):
                    if value > inp.max_value:
                        errors.append(
                            f"Input '{inp.name}' must be <= {inp.max_value}"
                        )
                
                # Choice validation
                if inp.choices and value not in inp.choices:
                    errors.append(
                        f"Input '{inp.name}' must be one of: {inp.choices}"
                    )
        
        return errors
    
    def __call__(self, **inputs) -> Dict[str, Any]:
        """Allow calling the tool instance directly."""
        return self.execute(**inputs)


class AgentToolBase(ToolBase):
    """
    Base class for agent-as-tool implementations.
    
    Agent tools wrap a sub-agent (e.g., an AI image generator) and expose
    it as a tool that can be used in pipelines.
    
    Example:
        class ImageGeneratorTool(AgentToolBase):
            tool_id = "ai_image_generator"
            name = "AI Image Generator"
            description = "Generates images using AI based on text prompts"
            
            inputs = [
                InputSchema(name="prompt", type=DataType.INSTRUCTIONS, required=True),
                InputSchema(name="style", type=DataType.STRING, default="realistic"),
            ]
            outputs = [
                OutputSchema(name="generated_image", type=DataType.IMAGE),
            ]
            
            def setup_agent(self):
                # Initialize the sub-agent
                from google.adk.agents.llm_agent import Agent
                self.agent = Agent(
                    model='gemini-2.0-flash',
                    name='image_generator',
                    instruction="Generate images based on prompts",
                )
            
            async def execute_agent(self, **inputs) -> Dict[str, Any]:
                # Run the sub-agent
                result = await self.agent.run(inputs["prompt"])
                return {"generated_image": result.image_path}
    """
    
    agent: Any = None  # The sub-agent instance
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setup_agent()
    
    def setup_agent(self) -> None:
        """
        Initialize the sub-agent.
        
        Override this method to set up your specific agent.
        """
        pass
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Generate schema with agent type."""
        schema = super().get_schema()
        schema.type = ToolType.AGENT
        return schema
    
    def execute(self, **inputs) -> Dict[str, Any]:
        """
        Execute the agent tool synchronously.
        
        Override execute_agent for async execution.
        """
        import asyncio
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            return asyncio.run_coroutine_threadsafe(
                self.execute_agent(**inputs), loop
            ).result()
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(self.execute_agent(**inputs))
    
    async def execute_agent(self, **inputs) -> Dict[str, Any]:
        """
        Execute the agent asynchronously.
        
        Override this method in subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute_agent")


def create_tool_schema(
    tool_id: str,
    name: str,
    description: str,
    inputs: List[InputSchema],
    outputs: List[OutputSchema],
    category: str = "general",
    tool_type: ToolType = ToolType.FUNCTION,
    **kwargs
) -> ToolSchema:
    """Helper function to create a tool schema."""
    return ToolSchema(
        tool_id=tool_id,
        name=name,
        description=description,
        type=tool_type,
        category=category,
        inputs=inputs,
        outputs=outputs,
        **kwargs
    )
