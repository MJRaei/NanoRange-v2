"""
Pipeline Manager - Creates and manipulates pipeline definitions.

Provides a high-level interface for building pipelines programmatically
or through the orchestrator agent.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from nanorange.core.schemas import (
    DataType,
    InputSource,
    Pipeline,
    PipelineStep,
    StepInput,
    StepStatus,
)
from nanorange.core.registry import ToolRegistry, get_registry
from nanorange.core.validator import PipelineValidator, ValidationResult


class PipelineManager:
    """
    Manager for creating and manipulating pipelines.
    
    This class provides a fluent interface for building pipelines
    and is used by the orchestrator's meta-tools.
    """
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        validator: Optional[PipelineValidator] = None
    ):
        """
        Initialize the pipeline manager.
        
        Args:
            registry: Tool registry (defaults to global)
            validator: Pipeline validator (creates new if not provided)
        """
        self.registry = registry or get_registry()
        self.validator = validator or PipelineValidator(self.registry)
        self._current_pipeline: Optional[Pipeline] = None
    
    @property
    def current_pipeline(self) -> Optional[Pipeline]:
        """Get the current working pipeline."""
        return self._current_pipeline
    
    def new_pipeline(
        self,
        name: str = "Untitled Pipeline",
        description: str = ""
    ) -> Pipeline:
        """
        Create a new empty pipeline.
        
        Args:
            name: Pipeline name
            description: Pipeline description
            
        Returns:
            The new pipeline
        """
        self._current_pipeline = Pipeline(
            name=name,
            description=description,
        )
        return self._current_pipeline
    
    def load_pipeline(self, pipeline: Pipeline) -> None:
        """Load an existing pipeline for editing."""
        self._current_pipeline = pipeline
    
    def add_step(
        self,
        tool_id: str,
        step_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        step_id: Optional[str] = None
    ) -> PipelineStep:
        """
        Add a step to the current pipeline.
        
        Args:
            tool_id: ID of the tool to use
            step_name: Human-readable name for this step
            inputs: Initial input values (converted to StepInput)
            step_id: Optional specific step ID
            
        Returns:
            The created step
            
        Raises:
            ValueError: If no pipeline is active or tool doesn't exist
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline. Call new_pipeline() first.")
        
        if not self.registry.has_tool(tool_id):
            raise ValueError(f"Unknown tool: {tool_id}")
        
        # Convert simple inputs to StepInput objects
        step_inputs: Dict[str, StepInput] = {}
        if inputs:
            for name, value in inputs.items():
                if isinstance(value, StepInput):
                    step_inputs[name] = value
                else:
                    step_inputs[name] = StepInput.static(value)
        
        # Create step
        step_kwargs = {
            "step_name": step_name,
            "tool_id": tool_id,
            "inputs": step_inputs,
        }
        if step_id:
            step_kwargs["step_id"] = step_id
        
        step = PipelineStep(**step_kwargs)
        self._current_pipeline.add_step(step)
        
        return step
    
    def connect_steps(
        self,
        from_step: str,
        output_name: str,
        to_step: str,
        input_name: str
    ) -> bool:
        """
        Connect an output of one step to an input of another.
        
        Args:
            from_step: Source step ID or name
            output_name: Output name from source step
            to_step: Target step ID or name
            input_name: Input name on target step
            
        Returns:
            True if connection was made
            
        Raises:
            ValueError: If steps not found or connection invalid
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        # Find steps by ID or name
        source = (
            self._current_pipeline.get_step(from_step) or
            self._current_pipeline.get_step_by_name(from_step)
        )
        target = (
            self._current_pipeline.get_step(to_step) or
            self._current_pipeline.get_step_by_name(to_step)
        )
        
        if not source:
            raise ValueError(f"Source step not found: {from_step}")
        if not target:
            raise ValueError(f"Target step not found: {to_step}")
        
        # Validate output exists on source
        source_schema = self.registry.get_schema(source.tool_id)
        if source_schema and not source_schema.get_output(output_name):
            raise ValueError(
                f"Tool '{source.tool_id}' has no output '{output_name}'"
            )
        
        # Validate input exists on target
        target_schema = self.registry.get_schema(target.tool_id)
        if target_schema and not target_schema.get_input(input_name):
            raise ValueError(
                f"Tool '{target.tool_id}' has no input '{input_name}'"
            )
        
        # Create connection
        target.inputs[input_name] = StepInput.from_step(
            source.step_id, output_name
        )
        
        self._current_pipeline.modified_at = datetime.utcnow()
        return True
    
    def set_parameter(
        self,
        step: str,
        param_name: str,
        value: Any
    ) -> bool:
        """
        Set a static parameter value on a step.
        
        Args:
            step: Step ID or name
            param_name: Parameter name
            value: Parameter value
            
        Returns:
            True if parameter was set
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        target = (
            self._current_pipeline.get_step(step) or
            self._current_pipeline.get_step_by_name(step)
        )
        
        if not target:
            raise ValueError(f"Step not found: {step}")
        
        target.inputs[param_name] = StepInput.static(value)
        self._current_pipeline.modified_at = datetime.utcnow()
        return True
    
    def set_user_input(
        self,
        step: str,
        param_name: str,
        prompt: str = ""
    ) -> bool:
        """
        Mark a parameter as requiring user input at runtime.
        
        Args:
            step: Step ID or name
            param_name: Parameter name
            prompt: Prompt to show user
            
        Returns:
            True if set successfully
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        target = (
            self._current_pipeline.get_step(step) or
            self._current_pipeline.get_step_by_name(step)
        )
        
        if not target:
            raise ValueError(f"Step not found: {step}")
        
        target.inputs[param_name] = StepInput.from_user(prompt)
        self._current_pipeline.modified_at = datetime.utcnow()
        return True
    
    def remove_step(self, step: str) -> bool:
        """
        Remove a step from the pipeline.
        
        Args:
            step: Step ID or name
            
        Returns:
            True if removed
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        target = (
            self._current_pipeline.get_step(step) or
            self._current_pipeline.get_step_by_name(step)
        )
        
        if not target:
            return False
        
        # Also remove connections to this step
        for other_step in self._current_pipeline.steps:
            inputs_to_remove = []
            for input_name, input_val in other_step.inputs.items():
                if (input_val.source == InputSource.STEP_OUTPUT and
                    input_val.source_step_id == target.step_id):
                    inputs_to_remove.append(input_name)
            
            for input_name in inputs_to_remove:
                del other_step.inputs[input_name]
        
        return self._current_pipeline.remove_step(target.step_id)
    
    def modify_step(
        self,
        step: str,
        new_tool_id: Optional[str] = None,
        new_name: Optional[str] = None
    ) -> bool:
        """
        Modify a step's properties.
        
        Args:
            step: Step ID or name
            new_tool_id: New tool ID (optional)
            new_name: New step name (optional)
            
        Returns:
            True if modified
        """
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        target = (
            self._current_pipeline.get_step(step) or
            self._current_pipeline.get_step_by_name(step)
        )
        
        if not target:
            return False
        
        if new_tool_id:
            if not self.registry.has_tool(new_tool_id):
                raise ValueError(f"Unknown tool: {new_tool_id}")
            target.tool_id = new_tool_id
            # Clear inputs since tool changed
            target.inputs.clear()
        
        if new_name:
            target.step_name = new_name
        
        self._current_pipeline.modified_at = datetime.utcnow()
        return True
    
    def validate(self) -> ValidationResult:
        """Validate the current pipeline."""
        if not self._current_pipeline:
            result = ValidationResult()
            result.add_error("No active pipeline")
            return result
        
        return self.validator.validate(self._current_pipeline)
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get a summary of the current pipeline."""
        if not self._current_pipeline:
            return {"error": "No active pipeline"}
        
        steps_summary = []
        for step in self._current_pipeline.steps:
            step_info = {
                "id": step.step_id,
                "name": step.step_name,
                "tool": step.tool_id,
                "status": step.status.value,
                "inputs": {}
            }
            
            for input_name, input_val in step.inputs.items():
                if input_val.source == InputSource.STATIC:
                    step_info["inputs"][input_name] = f"= {input_val.value}"
                elif input_val.source == InputSource.STEP_OUTPUT:
                    step_info["inputs"][input_name] = (
                        f"<- {input_val.source_step_id}.{input_val.source_output}"
                    )
                else:
                    step_info["inputs"][input_name] = "<user input>"
            
            steps_summary.append(step_info)
        
        return {
            "id": self._current_pipeline.pipeline_id,
            "name": self._current_pipeline.name,
            "description": self._current_pipeline.description,
            "steps": steps_summary,
            "created_at": self._current_pipeline.created_at.isoformat(),
            "modified_at": self._current_pipeline.modified_at.isoformat(),
        }
    
    def to_json(self) -> str:
        """Export current pipeline to JSON."""
        if not self._current_pipeline:
            raise ValueError("No active pipeline")
        
        return self._current_pipeline.model_dump_json(indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PipelineManager":
        """Create a manager with a pipeline loaded from JSON."""
        pipeline = Pipeline.model_validate_json(json_str)
        manager = cls()
        manager.load_pipeline(pipeline)
        return manager
