"""
Adaptive Executor - Pipeline execution with iterative refinement.

Executes pipelines with the ability to:
- Review outputs after each step
- Adjust parameters and re-run steps
- Remove tools that don't work for specific images
- Rebuild pipelines dynamically
"""

import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from nanorange.core.schemas import (
    DataType,
    InputSource,
    Pipeline,
    PipelineResult,
    PipelineStep,
    StepInput,
    StepResult,
    StepStatus,
    ToolSchema,
)
from nanorange.core.refinement_schemas import (
    RefinementAction,
    RefinementDecision,
    RefinementReport,
)
from nanorange.core.registry import ToolRegistry, get_registry
from nanorange.core.validator import PipelineValidator
from nanorange.agent.refinement.image_reviewer import ImageReviewer
from nanorange.agent.refinement.parameter_optimizer import ParameterOptimizer
from nanorange.agent.refinement.refinement_tracker import RefinementTracker
from nanorange import settings


class AdaptiveExecutionContext:
    """Context for adaptive pipeline execution."""
    
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.results: Dict[str, StepResult] = {}
        self.outputs: Dict[str, Dict[str, Any]] = {}
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Track removed steps
        self.removed_steps: List[str] = []
        
        # Track the input image for the pipeline (for comparison)
        self.input_image_path: Optional[str] = None
    
    def get_output(self, step_id: str, output_name: str) -> Any:
        """Get an output value from a completed step."""
        if step_id in self.removed_steps:
            raise ValueError(f"Step {step_id} was removed from pipeline")
        
        if step_id not in self.outputs:
            raise ValueError(f"Step {step_id} has not been executed")
        
        step_outputs = self.outputs[step_id]
        if output_name not in step_outputs:
            raise ValueError(f"Step {step_id} has no output '{output_name}'")
        
        return step_outputs[output_name]
    
    def mark_step_removed(self, step_id: str) -> None:
        """Mark a step as removed."""
        self.removed_steps.append(step_id)


class AdaptiveExecutor:
    """
    Executes pipelines with iterative refinement.
    
    Key features:
    - Reviews image outputs after each step
    - Adjusts parameters based on review feedback
    - Removes ineffective tools from the pipeline
    - Provides detailed refinement reports
    """
    
    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        validator: Optional[PipelineValidator] = None,
        reviewer: Optional[ImageReviewer] = None,
        optimizer: Optional[ParameterOptimizer] = None,
        user_input_handler: Optional[Callable[[str, str], Any]] = None,
        refinement_enabled: Optional[bool] = None,
        max_iterations: Optional[int] = None
    ):
        """
        Initialize the adaptive executor.
        
        Args:
            registry: Tool registry
            validator: Pipeline validator
            reviewer: Image reviewer for output assessment
            optimizer: Parameter optimizer
            user_input_handler: Function to get user input
            refinement_enabled: Whether to enable refinement (defaults to settings)
            max_iterations: Max iterations per tool (defaults to settings)
        """
        self.registry = registry or get_registry()
        self.validator = validator or PipelineValidator(self.registry)
        self.reviewer = reviewer or ImageReviewer()
        self.optimizer = optimizer or ParameterOptimizer()
        self.user_input_handler = user_input_handler
        
        self.refinement_enabled = (
            refinement_enabled if refinement_enabled is not None
            else settings.REFINEMENT_ENABLED
        )
        self.max_iterations = max_iterations or settings.MAX_TOOL_ITERATIONS
    
    def execute(
        self,
        pipeline: Pipeline,
        user_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
        stop_on_error: bool = True,
        context_description: Optional[str] = None
    ) -> Tuple[PipelineResult, RefinementReport]:
        """
        Execute a pipeline with adaptive refinement.
        
        Args:
            pipeline: The pipeline to execute
            user_inputs: Pre-provided user inputs
            stop_on_error: Whether to stop on first error
            context_description: Description of what the pipeline should achieve
            
        Returns:
            Tuple of (PipelineResult, RefinementReport)
        """
        # Initialize tracking
        tracker = RefinementTracker(pipeline.pipeline_id, pipeline.name)
        tracker.start_execution()
        
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
            result.step_results.append(StepResult(
                step_id="validation",
                step_name="Pipeline Validation",
                tool_id="validator",
                status=StepStatus.FAILED,
                error_message=str(validation),
            ))
            tracker.end_execution()
            return result, tracker.get_report()
        
        # Create execution context
        context = AdaptiveExecutionContext(pipeline)
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
            tracker.end_execution()
            return result, tracker.get_report()
        
        # Execute steps
        result.status = StepStatus.RUNNING
        
        for step_id in execution_order:
            # Skip removed steps
            if step_id in context.removed_steps:
                continue
            
            step = pipeline.get_step(step_id)
            if not step:
                continue
            
            # Execute with refinement
            step_result, was_removed = self._execute_step_with_refinement(
                step=step,
                context=context,
                user_inputs=user_inputs or {},
                tracker=tracker,
                context_description=context_description
            )
            
            if was_removed:
                # Step was removed, skip to next
                context.mark_step_removed(step_id)
                continue
            
            result.step_results.append(step_result)
            context.results[step_id] = step_result
            
            if step_result.status == StepStatus.COMPLETED:
                result.completed_steps += 1
                context.outputs[step_id] = step_result.outputs
            elif step_result.status == StepStatus.FAILED:
                result.failed_steps += 1
                if stop_on_error:
                    break
        
        # Finalize
        result.completed_at = datetime.utcnow()
        result.total_duration_seconds = (
            result.completed_at - result.started_at
        ).total_seconds()
        
        if result.failed_steps > 0:
            result.status = StepStatus.FAILED
        elif result.completed_steps == result.total_steps - len(context.removed_steps):
            result.status = StepStatus.COMPLETED
        else:
            result.status = StepStatus.PENDING
        
        tracker.end_execution()
        return result, tracker.get_report()
    
    def _execute_step_with_refinement(
        self,
        step: PipelineStep,
        context: AdaptiveExecutionContext,
        user_inputs: Dict[str, Dict[str, Any]],
        tracker: RefinementTracker,
        context_description: Optional[str]
    ) -> Tuple[StepResult, bool]:
        """
        Execute a single step with iterative refinement.
        
        Returns:
            Tuple of (StepResult, was_removed)
        """
        tool_schema = self.registry.get_schema(step.tool_id)
        
        # Resolve initial inputs
        resolved_inputs = self._resolve_inputs(step, context, user_inputs)
        
        # Identify user-locked parameters
        user_locked_params = self.optimizer.identify_locked_params(
            resolved_inputs, tool_schema
        ) if tool_schema else []
        
        # Start tracking this step
        tracker.start_step(
            step_id=step.step_id,
            step_name=step.step_name,
            tool_id=step.tool_id,
            user_locked_params=user_locked_params
        )
        
        # Track input image for the pipeline
        if context.input_image_path is None:
            for input_name, value in resolved_inputs.items():
                if isinstance(value, str) and any(
                    value.lower().endswith(ext) 
                    for ext in ['.png', '.jpg', '.jpeg', '.tif', '.tiff']
                ):
                    context.input_image_path = value
                    break
        
        # Refinement loop
        iteration = 1
        current_inputs = resolved_inputs.copy()
        final_result = None
        was_removed = False
        
        while iteration <= self.max_iterations:
            # Execute the step
            start_time = datetime.utcnow()
            step_result = self._execute_single_iteration(
                step=step,
                inputs=current_inputs
            )
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Check if step failed
            if step_result.status == StepStatus.FAILED:
                tracker.record_iteration(
                    iteration=iteration,
                    inputs_used=current_inputs,
                    outputs={},
                    duration_seconds=duration,
                    error=step_result.error_message
                )
                tracker.finalize_step(was_removed=False)
                return step_result, False
            
            # Check if refinement is enabled and output is an image
            should_review = (
                self.refinement_enabled and
                tool_schema and
                self._has_image_output(step_result.outputs, tool_schema)
            )
            
            if not should_review:
                # No review needed, accept result
                tracker.record_iteration(
                    iteration=iteration,
                    inputs_used=current_inputs,
                    outputs=step_result.outputs,
                    duration_seconds=duration
                )
                tracker.finalize_step(accepted_iteration=iteration)
                return step_result, False
            
            # Get output image path for review
            output_image_path = self._get_image_output_path(
                step_result.outputs, tool_schema
            )
            
            if not output_image_path:
                # No image to review
                tracker.record_iteration(
                    iteration=iteration,
                    inputs_used=current_inputs,
                    outputs=step_result.outputs,
                    duration_seconds=duration
                )
                tracker.finalize_step(accepted_iteration=iteration)
                return step_result, False
            
            # Review the output
            decision = self.reviewer.review_output(
                step_id=step.step_id,
                tool_schema=tool_schema,
                output_image_path=output_image_path,
                inputs_used=current_inputs,
                user_locked_params=user_locked_params,
                iteration=iteration,
                input_image_path=context.input_image_path,
                context=context_description
            )
            
            # Record this iteration
            tracker.record_iteration(
                iteration=iteration,
                inputs_used=current_inputs,
                outputs=step_result.outputs,
                decision=decision,
                duration_seconds=duration
            )
            
            # Act on the decision
            if decision.action == RefinementAction.ACCEPT:
                tracker.finalize_step(accepted_iteration=iteration)
                final_result = step_result
                break
            
            elif decision.action == RefinementAction.REMOVE_TOOL:
                tracker.record_tool_removal(
                    step_id=step.step_id,
                    tool_id=step.tool_id,
                    reason=decision.reasoning
                )
                tracker.finalize_step(
                    was_removed=True,
                    removal_reason=decision.reasoning
                )
                was_removed = True
                break
            
            elif decision.action == RefinementAction.ADJUST_PARAMS:
                if iteration < self.max_iterations:
                    # Apply parameter changes
                    current_inputs, _ = self.optimizer.apply_changes(
                        current_inputs,
                        decision,
                        tool_schema,
                        user_locked_params
                    )
                    iteration += 1
                else:
                    # Max iterations reached, accept current result
                    tracker.finalize_step(accepted_iteration=iteration)
                    final_result = step_result
                    break
            
            elif decision.action == RefinementAction.FAIL:
                step_result.status = StepStatus.FAILED
                step_result.error_message = f"Refinement failed: {decision.reasoning}"
                tracker.finalize_step(was_removed=False)
                return step_result, False
        
        if final_result is None:
            final_result = step_result
        
        return final_result, was_removed
    
    def _execute_single_iteration(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any]
    ) -> StepResult:
        """Execute a single iteration of a step."""
        result = StepResult(
            step_id=step.step_id,
            step_name=step.step_name,
            tool_id=step.tool_id,
            status=StepStatus.RUNNING,
            resolved_inputs=inputs.copy()
        )
        result.started_at = datetime.utcnow()
        
        try:
            # Get tool implementation
            implementation = self.registry.get_implementation(step.tool_id)
            if not implementation:
                tool_class = self.registry.get_tool_class(step.tool_id)
                if tool_class:
                    implementation = tool_class().execute
                else:
                    raise ValueError(
                        f"No implementation found for tool: {step.tool_id}"
                    )
            
            # Execute tool
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
    
    def _resolve_inputs(
        self,
        step: PipelineStep,
        context: AdaptiveExecutionContext,
        user_inputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve all inputs for a step."""
        resolved = {}
        
        # Get tool schema for defaults
        schema = self.registry.get_schema(step.tool_id)
        
        # Apply defaults from schema
        if schema:
            for inp in schema.inputs:
                if not inp.required and inp.default is not None:
                    resolved[inp.name] = inp.default
        
        # Resolve explicit inputs
        for input_name, step_input in step.inputs.items():
            if step_input.source == InputSource.STATIC:
                resolved[input_name] = step_input.value
            
            elif step_input.source == InputSource.STEP_OUTPUT:
                # Skip if source step was removed
                if step_input.source_step_id in context.removed_steps:
                    # Try to get from an earlier step
                    continue
                resolved[input_name] = context.get_output(
                    step_input.source_step_id,
                    step_input.source_output
                )
            
            elif step_input.source == InputSource.USER_INPUT:
                if (step.step_id in user_inputs and
                    input_name in user_inputs[step.step_id]):
                    resolved[input_name] = user_inputs[step.step_id][input_name]
                elif self.user_input_handler:
                    prompt = step_input.prompt or f"Enter value for {input_name}:"
                    resolved[input_name] = self.user_input_handler(
                        prompt, input_name
                    )
                else:
                    raise ValueError(
                        f"User input required for {input_name} "
                        "but no handler provided"
                    )
        
        return resolved
    
    def _has_image_output(
        self,
        outputs: Dict[str, Any],
        tool_schema: ToolSchema
    ) -> bool:
        """Check if the tool outputs include an image."""
        image_types = {DataType.IMAGE, DataType.MASK}
        
        for output in tool_schema.outputs:
            if output.type in image_types and output.name in outputs:
                return True
        
        return False
    
    def _get_image_output_path(
        self,
        outputs: Dict[str, Any],
        tool_schema: ToolSchema
    ) -> Optional[str]:
        """Get the path to an image output."""
        image_types = {DataType.IMAGE, DataType.MASK}
        
        for output in tool_schema.outputs:
            if output.type in image_types and output.name in outputs:
                value = outputs[output.name]
                if isinstance(value, str):
                    return value
        
        return None
