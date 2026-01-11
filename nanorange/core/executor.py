"""
Pipeline Executor - Executes validated pipelines.

Handles:
- Topological sorting for execution order
- Input resolution (connecting outputs to inputs)
- Tool execution with error handling
- Result collection and storage
"""

import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from nanorange.core.schemas import (
    InputSource,
    Pipeline,
    PipelineResult,
    PipelineStep,
    StepResult,
    StepStatus,
)
from nanorange.core.registry import ToolRegistry, get_registry
from nanorange.core.validator import PipelineValidator


class ExecutionContext:
    """Context for a single pipeline execution."""
    
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.results: Dict[str, StepResult] = {}
        self.outputs: Dict[str, Dict[str, Any]] = {}  # step_id -> {output_name: value}
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def get_output(self, step_id: str, output_name: str) -> Any:
        """Get an output value from a completed step."""
        if step_id not in self.outputs:
            raise ValueError(f"Step {step_id} has not been executed")
        
        step_outputs = self.outputs[step_id]
        if output_name not in step_outputs:
            raise ValueError(
                f"Step {step_id} has no output '{output_name}'"
            )
        
        return step_outputs[output_name]


class PipelineExecutor:
    """
    Executes pipelines by running tools in topological order.
    
    The executor:
    1. Validates the pipeline
    2. Determines execution order (topological sort)
    3. For each step:
       - Resolves inputs from previous outputs or static values
       - Executes the tool
       - Stores the results
    4. Returns a complete execution result
    """
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        validator: Optional[PipelineValidator] = None,
        user_input_handler: Optional[Callable[[str, str], Any]] = None
    ):
        """
        Initialize the executor.
        
        Args:
            registry: Tool registry (defaults to global)
            validator: Pipeline validator
            user_input_handler: Function to get user input (prompt, param_name) -> value
        """
        self.registry = registry or get_registry()
        self.validator = validator or PipelineValidator(self.registry)
        self.user_input_handler = user_input_handler
    
    def execute(
        self,
        pipeline: Pipeline,
        user_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
        stop_on_error: bool = True
    ) -> PipelineResult:
        """
        Execute a pipeline.
        
        Args:
            pipeline: The pipeline to execute
            user_inputs: Pre-provided user inputs {step_id: {param_name: value}}
            stop_on_error: Whether to stop on first error
            
        Returns:
            PipelineResult with all step results
        """
        # Initialize result
        result = PipelineResult(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.name,
            status=StepStatus.PENDING,
            total_steps=len(pipeline.steps),
        )
        result.started_at = datetime.utcnow()
        
        # Validate pipeline
        validation = self.validator.validate(pipeline)
        if not validation.is_valid:
            result.status = StepStatus.FAILED
            result.completed_at = datetime.utcnow()
            # Create a pseudo-result for validation failure
            result.step_results.append(StepResult(
                step_id="validation",
                step_name="Pipeline Validation",
                tool_id="validator",
                status=StepStatus.FAILED,
                error_message=str(validation),
            ))
            return result
        
        # Create execution context
        context = ExecutionContext(pipeline)
        context.started_at = datetime.utcnow()
        
        # Get execution order
        try:
            execution_order = self.validator.get_execution_order(pipeline)
        except ValueError as e:
            result.status = StepStatus.FAILED
            result.step_results.append(StepResult(
                step_id="ordering",
                step_name="Execution Order",
                tool_id="executor",
                status=StepStatus.FAILED,
                error_message=str(e),
            ))
            return result
        
        # Execute steps in order
        result.status = StepStatus.RUNNING
        
        for step_id in execution_order:
            step = pipeline.get_step(step_id)
            if not step:
                continue
            
            step_result = self._execute_step(
                step, context, user_inputs or {}
            )
            result.step_results.append(step_result)
            context.results[step_id] = step_result
            
            if step_result.status == StepStatus.COMPLETED:
                result.completed_steps += 1
                context.outputs[step_id] = step_result.outputs
            elif step_result.status == StepStatus.FAILED:
                result.failed_steps += 1
                if stop_on_error:
                    break
        
        # Finalize result
        result.completed_at = datetime.utcnow()
        result.total_duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()
        
        if result.failed_steps > 0:
            result.status = StepStatus.FAILED
        elif result.completed_steps == result.total_steps:
            result.status = StepStatus.COMPLETED
        else:
            result.status = StepStatus.PENDING  # Partially complete
        
        return result
    
    def _execute_step(
        self,
        step: PipelineStep,
        context: ExecutionContext,
        user_inputs: Dict[str, Dict[str, Any]]
    ) -> StepResult:
        """Execute a single pipeline step."""
        result = StepResult(
            step_id=step.step_id,
            step_name=step.step_name,
            tool_id=step.tool_id,
            status=StepStatus.RUNNING,
        )
        result.started_at = datetime.utcnow()
        
        # Update step status
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        try:
            # Resolve inputs
            resolved_inputs = self._resolve_inputs(step, context, user_inputs)
            result.resolved_inputs = resolved_inputs
            
            # Get tool implementation
            implementation = self.registry.get_implementation(step.tool_id)
            if not implementation:
                # Try to get tool class and instantiate
                tool_class = self.registry.get_tool_class(step.tool_id)
                if tool_class:
                    tool_instance = tool_class()
                    implementation = tool_instance.execute
                else:
                    raise ValueError(
                        f"No implementation found for tool: {step.tool_id}"
                    )
            
            # Execute tool
            outputs = implementation(**resolved_inputs)
            
            # Validate outputs is a dict
            if not isinstance(outputs, dict):
                outputs = {"result": outputs}
            
            result.outputs = outputs
            result.status = StepStatus.COMPLETED
            step.status = StepStatus.COMPLETED
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            step.status = StepStatus.FAILED
            step.error_message = str(e)
        
        finally:
            result.completed_at = datetime.utcnow()
            step.completed_at = datetime.utcnow()
            if result.started_at:
                result.duration_seconds = (
                    result.completed_at - result.started_at
                ).total_seconds()
        
        return result
    
    def _resolve_inputs(
        self,
        step: PipelineStep,
        context: ExecutionContext,
        user_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve all inputs for a step."""
        resolved = {}
        
        # Get tool schema for defaults
        schema = self.registry.get_schema(step.tool_id)
        
        # First, apply defaults from schema
        if schema:
            for inp in schema.inputs:
                if not inp.required and inp.default is not None:
                    resolved[inp.name] = inp.default
        
        # Then, resolve explicit inputs
        for input_name, step_input in step.inputs.items():
            if step_input.source == InputSource.STATIC:
                resolved[input_name] = step_input.value
            
            elif step_input.source == InputSource.STEP_OUTPUT:
                resolved[input_name] = context.get_output(
                    step_input.source_step_id,
                    step_input.source_output
                )
            
            elif step_input.source == InputSource.USER_INPUT:
                # Check pre-provided user inputs
                if (step.step_id in user_inputs and
                    input_name in user_inputs[step.step_id]):
                    resolved[input_name] = user_inputs[step.step_id][input_name]
                elif self.user_input_handler:
                    # Request from user
                    prompt = step_input.prompt or f"Enter value for {input_name}:"
                    resolved[input_name] = self.user_input_handler(
                        prompt, input_name
                    )
                else:
                    raise ValueError(
                        f"User input required for {input_name} but no handler provided"
                    )
        
        return resolved
    
    def execute_single_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any]
    ) -> StepResult:
        """
        Execute a single step with explicit inputs (for testing/debugging).
        
        Args:
            step: The step to execute
            inputs: Direct input values
            
        Returns:
            StepResult
        """
        result = StepResult(
            step_id=step.step_id,
            step_name=step.step_name,
            tool_id=step.tool_id,
            status=StepStatus.RUNNING,
            resolved_inputs=inputs,
        )
        result.started_at = datetime.utcnow()
        
        try:
            implementation = self.registry.get_implementation(step.tool_id)
            if not implementation:
                tool_class = self.registry.get_tool_class(step.tool_id)
                if tool_class:
                    implementation = tool_class().execute
                else:
                    raise ValueError(f"No implementation for: {step.tool_id}")
            
            outputs = implementation(**inputs)
            if not isinstance(outputs, dict):
                outputs = {"result": outputs}
            
            result.outputs = outputs
            result.status = StepStatus.COMPLETED
            
        except Exception as e:
            result.status = StepStatus.FAILED
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
        
        finally:
            result.completed_at = datetime.utcnow()
            if result.started_at:
                result.duration_seconds = (
                    result.completed_at - result.started_at
                ).total_seconds()
        
        return result
