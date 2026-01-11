"""
Pydantic schemas for tools, pipelines, steps, and results.

These schemas define the contract between tools and the pipeline system,
ensuring type safety and clear documentation of inputs/outputs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from uuid import uuid4


class DataType(str, Enum):
    """Supported data types for tool inputs and outputs."""
    
    IMAGE = "image"           # File path to an image
    MASK = "mask"             # Binary mask image path
    FLOAT = "float"           # Floating point number
    INT = "int"               # Integer
    STRING = "string"         # Text string
    BOOL = "bool"             # Boolean
    LIST = "list"             # List of values
    DICT = "dict"             # Dictionary/JSON object
    PATH = "path"             # Generic file path
    ARRAY = "array"           # Numpy array (stored as file)
    MEASUREMENTS = "measurements"  # Measurement results (dict/dataframe)
    PARAMETERS = "parameters"      # Parameter dictionary
    INSTRUCTIONS = "instructions"  # Text instructions for agent tools


class ToolType(str, Enum):
    """Type of tool implementation."""
    
    FUNCTION = "function"     # Simple function tool
    AGENT = "agent"           # Agent-as-tool (sub-agent)


class InputSchema(BaseModel):
    """Schema for a single tool input."""
    
    name: str = Field(..., description="Input parameter name")
    type: DataType = Field(..., description="Data type of the input")
    description: str = Field("", description="Human-readable description")
    required: bool = Field(True, description="Whether input is required")
    default: Optional[Any] = Field(None, description="Default value if not required")
    
    # Constraints for numeric types
    min_value: Optional[float] = Field(None, description="Minimum value (for numeric)")
    max_value: Optional[float] = Field(None, description="Maximum value (for numeric)")
    
    # Constraints for string/enum types
    choices: Optional[List[str]] = Field(None, description="Allowed values")
    
    model_config = {"extra": "forbid"}


class OutputSchema(BaseModel):
    """Schema for a single tool output."""
    
    name: str = Field(..., description="Output name")
    type: DataType = Field(..., description="Data type of the output")
    description: str = Field("", description="Human-readable description")
    
    model_config = {"extra": "forbid"}


class ToolSchema(BaseModel):
    """Complete schema for a registered tool."""
    
    tool_id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Human-readable tool name")
    description: str = Field(..., description="Detailed description of what the tool does")
    type: ToolType = Field(ToolType.FUNCTION, description="Tool implementation type")
    category: str = Field("general", description="Tool category for organization")
    
    inputs: List[InputSchema] = Field(default_factory=list, description="Input parameters")
    outputs: List[OutputSchema] = Field(default_factory=list, description="Output values")
    
    # Metadata
    version: str = Field("1.0.0", description="Tool version")
    author: Optional[str] = Field(None, description="Tool author")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    
    model_config = {"extra": "forbid"}
    
    def get_input(self, name: str) -> Optional[InputSchema]:
        """Get input schema by name."""
        for inp in self.inputs:
            if inp.name == name:
                return inp
        return None
    
    def get_output(self, name: str) -> Optional[OutputSchema]:
        """Get output schema by name."""
        for out in self.outputs:
            if out.name == name:
                return out
        return None
    
    def to_description(self) -> str:
        """Generate a description string for the LLM."""
        lines = [
            f"Tool: {self.name} ({self.tool_id})",
            f"Description: {self.description}",
            f"Category: {self.category}",
            "Inputs:"
        ]
        for inp in self.inputs:
            req = "required" if inp.required else f"optional, default={inp.default}"
            lines.append(f"  - {inp.name} ({inp.type.value}): {inp.description} [{req}]")
        lines.append("Outputs:")
        for out in self.outputs:
            lines.append(f"  - {out.name} ({out.type.value}): {out.description}")
        return "\n".join(lines)


# ============================================================================
# Pipeline Schemas
# ============================================================================

class InputSource(str, Enum):
    """Source type for a step input."""
    
    STATIC = "static"         # Static value provided directly
    STEP_OUTPUT = "step_output"  # Output from another step
    USER_INPUT = "user_input"    # Provided by user at runtime


class StepInput(BaseModel):
    """Defines where a step gets its input from."""
    
    source: InputSource = Field(..., description="Source of the input value")
    
    # For STATIC source
    value: Optional[Any] = Field(None, description="Static value")
    
    # For STEP_OUTPUT source
    source_step_id: Optional[str] = Field(None, description="Source step ID")
    source_output: Optional[str] = Field(None, description="Output name from source step")
    
    # For USER_INPUT source
    prompt: Optional[str] = Field(None, description="Prompt to show user")
    
    model_config = {"extra": "forbid"}
    
    @classmethod
    def static(cls, value: Any) -> "StepInput":
        """Create a static input."""
        return cls(source=InputSource.STATIC, value=value)
    
    @classmethod
    def from_step(cls, step_id: str, output_name: str) -> "StepInput":
        """Create an input from another step's output."""
        return cls(
            source=InputSource.STEP_OUTPUT,
            source_step_id=step_id,
            source_output=output_name
        )
    
    @classmethod
    def from_user(cls, prompt: str = "") -> "StepInput":
        """Create a user input."""
        return cls(source=InputSource.USER_INPUT, prompt=prompt)


class StepStatus(str, Enum):
    """Execution status of a pipeline step."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStep(BaseModel):
    """A single step in a pipeline."""
    
    step_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    step_name: str = Field(..., description="Human-readable step name")
    tool_id: str = Field(..., description="ID of the tool to use")
    
    inputs: Dict[str, StepInput] = Field(
        default_factory=dict,
        description="Input mappings (input_name -> StepInput)"
    )
    
    status: StepStatus = Field(StepStatus.PENDING, description="Execution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Execution metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = {"extra": "forbid"}


class Pipeline(BaseModel):
    """Complete pipeline definition."""
    
    pipeline_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field("Untitled Pipeline", description="Pipeline name")
    description: str = Field("", description="Pipeline description")
    
    steps: List[PipelineStep] = Field(default_factory=list, description="Pipeline steps")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"extra": "forbid"}
    
    def get_step(self, step_id: str) -> Optional[PipelineStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_step_by_name(self, name: str) -> Optional[PipelineStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.step_name == name:
                return step
        return None
    
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline."""
        self.steps.append(step)
        self.modified_at = datetime.utcnow()
    
    def remove_step(self, step_id: str) -> bool:
        """Remove a step by ID."""
        for i, step in enumerate(self.steps):
            if step.step_id == step_id:
                self.steps.pop(i)
                self.modified_at = datetime.utcnow()
                return True
        return False


# ============================================================================
# Result Schemas
# ============================================================================

class StepResult(BaseModel):
    """Result of executing a single step."""
    
    step_id: str
    step_name: str
    tool_id: str
    status: StepStatus
    
    # Actual output values (output_name -> value/path)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Resolved input values that were used
    resolved_inputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Error info
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    model_config = {"extra": "forbid"}


class PipelineResult(BaseModel):
    """Result of executing a complete pipeline."""
    
    pipeline_id: str
    pipeline_name: str
    
    status: StepStatus  # Overall status
    step_results: List[StepResult] = Field(default_factory=list)
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    
    # Summary
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    
    model_config = {"extra": "forbid"}
    
    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Get result for a specific step."""
        for result in self.step_results:
            if result.step_id == step_id:
                return result
        return None
    
    def get_final_outputs(self) -> Dict[str, Any]:
        """Get outputs from all completed steps."""
        outputs = {}
        for result in self.step_results:
            if result.status == StepStatus.COMPLETED:
                outputs[result.step_name] = result.outputs
        return outputs
