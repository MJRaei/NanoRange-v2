"""
Meta-tools for pipeline manipulation.

These tools are used by the orchestrator agent to:
- Discover available tools
- Build and modify pipelines
- Execute and validate pipelines
- Save and load pipeline templates
- Execute with iterative refinement
"""

from typing import Any, Dict, List, Optional
from nanorange.core.schemas import Pipeline, PipelineStep, StepInput, InputSource
from nanorange.core.registry import get_registry
from nanorange.core.pipeline import PipelineManager
from nanorange.core.executor import PipelineExecutor
from nanorange.storage.session_manager import SessionManager
from nanorange.agent.refinement import AdaptiveExecutor
from nanorange.core.refinement_schemas import RefinementReport


_current_manager: Optional[PipelineManager] = None
_current_session: Optional[SessionManager] = None
_current_executor: Optional[PipelineExecutor] = None
_current_adaptive_executor: Optional[AdaptiveExecutor] = None
_last_refinement_report: Optional[RefinementReport] = None
_session_image_path: Optional[str] = None


def set_session_image_path(image_path: str) -> None:
    """
    Set the current session image path.
    
    This is called by the orchestrator when an image is provided via the API.
    The path is then available for automatic injection into pipeline steps.
    
    Args:
        image_path: Absolute path to the image file
    """
    global _session_image_path
    _session_image_path = image_path


def get_session_image_path() -> Optional[str]:
    """
    Get the current session image path.
    
    Returns:
        The current image path, or None if no image has been set
    """
    return _session_image_path


def clear_session_image_path() -> None:
    """Clear the session image path."""
    global _session_image_path
    _session_image_path = None


def _get_manager() -> PipelineManager:
    """Get or create the current pipeline manager."""
    global _current_manager
    if _current_manager is None:
        _current_manager = PipelineManager()
    return _current_manager


def _get_session() -> SessionManager:
    """Get or create the current session manager."""
    global _current_session
    if _current_session is None:
        _current_session = SessionManager()
        _current_session.create_session()
    return _current_session


def _get_executor() -> PipelineExecutor:
    """Get or create the pipeline executor."""
    global _current_executor
    if _current_executor is None:
        # Use session_id from the current session to ensure files are saved to the correct folder
        session = _get_session()
        _current_executor = PipelineExecutor(session_id=session.session_id)
    return _current_executor


def _get_adaptive_executor() -> AdaptiveExecutor:
    """Get or create the adaptive executor with refinement support."""
    global _current_adaptive_executor
    if _current_adaptive_executor is None:
        _current_adaptive_executor = AdaptiveExecutor()
    return _current_adaptive_executor


def initialize_session(session_id: Optional[str] = None) -> str:
    """
    Initialize or resume a session.
    
    Args:
        session_id: Optional existing session ID to resume
        
    Returns:
        The session ID
    """
    global _current_session, _current_manager, _session_image_path
    
    registry = get_registry()
    registry.discover_tools()
    
    if session_id:
        try:
            _current_session = SessionManager(session_id=session_id)
        except ValueError:
            _current_session = SessionManager()
            _current_session.create_session()
            # Clear image path for new sessions
            _session_image_path = None
    else:
        _current_session = SessionManager()
        _current_session.create_session()
        # Clear image path for new sessions
        _session_image_path = None
    
    _current_manager = PipelineManager()
    return _current_session.session_id


def get_current_image_path() -> Dict[str, Any]:
    """
    Get the current session image path.
    
    Use this to retrieve the path of the image that was provided
    by the user (via upload or attachment). This path can be used
    directly in the load_image step.
    
    Returns:
        Dictionary with image path or status message
    """
    path = get_session_image_path()
    if path:
        return {
            "status": "available",
            "image_path": path,
            "message": "Use this path in the load_image step's image_path parameter."
        }
    else:
        return {
            "status": "not_available",
            "image_path": None,
            "message": "No image has been attached in this session. Ask the user to provide an image."
        }


def list_available_tools(category: Optional[str] = None) -> Dict[str, Any]:
    """
    List all available tools in the registry.
    
    Args:
        category: Optional category to filter by (e.g., "preprocessing", 
                  "segmentation", "measurement")
    
    Returns:
        Dictionary containing:
        - tools: List of tool summaries
        - categories: List of available categories
        - total_count: Total number of tools
    """
    registry = get_registry()
    tools = registry.list_tools(category=category)
    
    tool_summaries = []
    for tool in tools:
        tool_summaries.append({
            "tool_id": tool.tool_id,
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "type": tool.type.value,
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type.value,
                    "required": inp.required,
                    "description": inp.description,
                }
                for inp in tool.inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type.value,
                    "description": out.description,
                }
                for out in tool.outputs
            ],
        })
    
    return {
        "tools": tool_summaries,
        "categories": registry.list_categories(),
        "total_count": len(tool_summaries),
    }


def get_tool_details(tool_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_id: The tool identifier
        
    Returns:
        Full tool schema or error message
    """
    registry = get_registry()
    schema = registry.get_schema(tool_id)
    
    if not schema:
        return {"error": f"Tool not found: {tool_id}"}
    
    return {
        "tool_id": schema.tool_id,
        "name": schema.name,
        "description": schema.description,
        "type": schema.type.value,
        "category": schema.category,
        "version": schema.version,
        "tags": schema.tags,
        "inputs": [inp.model_dump(mode='json') for inp in schema.inputs],
        "outputs": [out.model_dump(mode='json') for out in schema.outputs],
    }


def new_pipeline(name: str = "New Pipeline", description: str = "") -> Dict[str, Any]:
    """
    Create a new empty pipeline.
    
    Args:
        name: Human-readable name for the pipeline
        description: Description of what the pipeline does
        
    Returns:
        Pipeline summary
    """
    manager = _get_manager()
    pipeline = manager.new_pipeline(name=name, description=description)
    
    return {
        "status": "created",
        "pipeline_id": pipeline.pipeline_id,
        "name": pipeline.name,
        "description": pipeline.description,
    }


def create_step(
    tool_id: str,
    step_name: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add a new step to the current pipeline.
    
    Args:
        tool_id: ID of the tool to use (from list_available_tools)
        step_name: Human-readable name for this step
        parameters: Optional dictionary of parameter values to set
        
    Returns:
        Step information including step_id
    """
    manager = _get_manager()
    
    if not manager.current_pipeline:
        manager.new_pipeline()
    
    try:
        step = manager.add_step(
            tool_id=tool_id,
            step_name=step_name,
            inputs=parameters
        )
        
        return {
            "status": "created",
            "step_id": step.step_id,
            "step_name": step.step_name,
            "tool_id": step.tool_id,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def connect_steps(
    from_step: str,
    output_name: str,
    to_step: str,
    input_name: str
) -> Dict[str, Any]:
    """
    Connect the output of one step to the input of another.
    
    Args:
        from_step: Source step name or ID
        output_name: Name of the output from source step
        to_step: Target step name or ID
        input_name: Name of the input on target step
        
    Returns:
        Connection status
    """
    manager = _get_manager()
    
    try:
        manager.connect_steps(from_step, output_name, to_step, input_name)
        return {
            "status": "connected",
            "connection": f"{from_step}.{output_name} -> {to_step}.{input_name}"
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def set_parameter(
    step: str,
    param_name: str,
    value: Any
) -> Dict[str, Any]:
    """
    Set a parameter value on a step.
    
    Args:
        step: Step name or ID
        param_name: Parameter name
        value: Parameter value
        
    Returns:
        Status
    """
    manager = _get_manager()
    
    try:
        manager.set_parameter(step, param_name, value)
        return {
            "status": "set",
            "step": step,
            "parameter": param_name,
            "value": value
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def modify_step(
    step: str,
    new_tool_id: Optional[str] = None,
    new_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Modify an existing step.
    
    Args:
        step: Step name or ID
        new_tool_id: New tool to use (clears existing inputs)
        new_name: New step name
        parameters: New parameter values to set
        
    Returns:
        Status
    """
    manager = _get_manager()
    
    try:
        if new_tool_id or new_name:
            manager.modify_step(step, new_tool_id=new_tool_id, new_name=new_name)
        
        if parameters:
            for name, value in parameters.items():
                manager.set_parameter(step, name, value)
        
        return {"status": "modified", "step": step}
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def remove_step(step: str) -> Dict[str, Any]:
    """
    Remove a step from the pipeline.
    
    Args:
        step: Step name or ID
        
    Returns:
        Status
    """
    manager = _get_manager()
    
    success = manager.remove_step(step)
    if success:
        return {"status": "removed", "step": step}
    else:
        return {"status": "error", "message": f"Step not found: {step}"}


def validate_pipeline() -> Dict[str, Any]:
    """
    Validate the current pipeline.
    
    Checks for:
    - Valid tool references
    - Required inputs are provided
    - Type compatibility between connections
    - No circular dependencies
    
    Returns:
        Validation result
    """
    manager = _get_manager()
    result = manager.validate()
    
    return {
        "is_valid": result.is_valid,
        "errors": [str(e) for e in result.errors],
        "warnings": [str(w) for w in result.warnings],
    }


def _inject_session_image_path(
    manager: PipelineManager,
    user_inputs: Optional[Dict[str, Dict[str, Any]]]
) -> Dict[str, Dict[str, Any]]:
    """
    Inject the session image path into load_image steps if not already set.
    
    This provides automatic image path resolution for pipelines when:
    1. An image was provided via the API
    2. The load_image step doesn't have a path set
    
    Args:
        manager: The pipeline manager
        user_inputs: Existing user inputs
        
    Returns:
        Updated user_inputs dict with injected image paths
    """
    if user_inputs is None:
        user_inputs = {}
    
    session_image = get_session_image_path()
    if not session_image:
        return user_inputs
    
    # Find load_image steps that need the image path
    if not manager.current_pipeline:
        return user_inputs
    
    for step in manager.current_pipeline.steps:
        if step.tool_id == "load_image":
            step_id = step.step_id
            
            # Check if image_path is already set in inputs
            has_static_path = (
                "image_path" in step.inputs and 
                step.inputs["image_path"].value is not None
            )
            
            # Check if it's already in user_inputs
            has_user_path = (
                step_id in user_inputs and 
                "image_path" in user_inputs[step_id]
            )
            
            # Inject session image path if not already set
            if not has_static_path and not has_user_path:
                if step_id not in user_inputs:
                    user_inputs[step_id] = {}
                user_inputs[step_id]["image_path"] = session_image
    
    return user_inputs


def execute_pipeline(
    user_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
    stop_on_error: bool = True
) -> Dict[str, Any]:
    """
    Execute the current pipeline.
    
    Args:
        user_inputs: Pre-provided values for user-input parameters
                    Format: {step_id: {param_name: value}}
        stop_on_error: Whether to stop execution on first error
        
    Returns:
        Execution result with step outputs
    """
    manager = _get_manager()
    executor = _get_executor()
    
    if not manager.current_pipeline:
        return {"status": "error", "message": "No active pipeline"}
    
    user_inputs = _inject_session_image_path(manager, user_inputs)
    
    validation = manager.validate()
    if not validation.is_valid:
        return {
            "status": "validation_failed",
            "errors": [str(e) for e in validation.errors],
        }
    
    result = executor.execute(
        manager.current_pipeline,
        user_inputs=user_inputs,
        stop_on_error=stop_on_error
    )
    
    session = _get_session()
    session.save_pipeline(manager.current_pipeline)
    session.save_result(result)
    
    step_summaries = []
    for sr in result.step_results:
        step_summaries.append({
            "step_name": sr.step_name,
            "tool_id": sr.tool_id,
            "status": sr.status.value,
            "duration_seconds": sr.duration_seconds,
            "outputs": sr.outputs,
            "error": sr.error_message,
        })
    
    return {
        "status": result.status.value,
        "pipeline_name": result.pipeline_name,
        "total_steps": result.total_steps,
        "completed_steps": result.completed_steps,
        "failed_steps": result.failed_steps,
        "total_duration_seconds": result.total_duration_seconds,
        "step_results": step_summaries,
    }


def execute_pipeline_adaptive(
    user_inputs: Optional[Dict[str, Dict[str, Any]]] = None,
    stop_on_error: bool = True,
    context_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the current pipeline with iterative refinement.
    
    This advanced execution mode:
    - Reviews image outputs after each step using a vision model
    - Adjusts parameters automatically to improve results
    - Removes tools that don't work for the specific image
    - Provides detailed reports of all changes made
    
    Note: Only parameters NOT explicitly specified by the user will be adjusted.
    User-provided values are treated as locked and won't be modified.
    
    Args:
        user_inputs: Pre-provided values for user-input parameters
                    Format: {step_id: {param_name: value}}
        stop_on_error: Whether to stop execution on first error
        context_description: Description of what the pipeline should achieve,
                           helps the reviewer make better decisions
        
    Returns:
        Execution result with step outputs and refinement report
    """
    global _last_refinement_report
    
    manager = _get_manager()
    adaptive_executor = _get_adaptive_executor()
    
    if not manager.current_pipeline:
        return {"status": "error", "message": "No active pipeline"}
    
    user_inputs = _inject_session_image_path(manager, user_inputs)
    
    validation = manager.validate()
    if not validation.is_valid:
        return {
            "status": "validation_failed",
            "errors": [str(e) for e in validation.errors],
        }
    
    # Execute with refinement
    result, refinement_report = adaptive_executor.execute(
        manager.current_pipeline,
        user_inputs=user_inputs,
        stop_on_error=stop_on_error,
        context_description=context_description
    )
    
    # Store for later retrieval
    _last_refinement_report = refinement_report
    
    # Save results
    session = _get_session()
    session.save_pipeline(manager.current_pipeline)
    session.save_result(result)
    
    # Build step summaries
    step_summaries = []
    for sr in result.step_results:
        step_summaries.append({
            "step_name": sr.step_name,
            "tool_id": sr.tool_id,
            "status": sr.status.value,
            "duration_seconds": sr.duration_seconds,
            "outputs": sr.outputs,
            "error": sr.error_message,
        })
    
    # Get refinement summary
    refinement_summary = refinement_report.get_summary()
    
    return {
        "status": result.status.value,
        "pipeline_name": result.pipeline_name,
        "total_steps": result.total_steps,
        "completed_steps": result.completed_steps,
        "failed_steps": result.failed_steps,
        "total_duration_seconds": result.total_duration_seconds,
        "step_results": step_summaries,
        "refinement": {
            "enabled": True,
            "total_iterations": refinement_summary["total_iterations"],
            "steps_refined": refinement_summary["steps_refined"],
            "tools_removed": refinement_summary["tools_removed"],
            "tools_added": refinement_summary["tools_added"],
            "changes": refinement_summary["step_changes"],
            "pipeline_modifications": refinement_summary["pipeline_modifications"],
        }
    }


def get_refinement_report() -> Dict[str, Any]:
    """
    Get the detailed refinement report from the last adaptive execution.
    
    Returns detailed information about:
    - All parameter changes made and why
    - Tools that were removed and the reasons
    - Tools that were added
    - Iteration history for each step
    
    Returns:
        Detailed refinement report or error if no report available
    """
    global _last_refinement_report
    
    if _last_refinement_report is None:
        return {
            "status": "error",
            "message": "No refinement report available. Run execute_pipeline_adaptive first."
        }
    
    return {
        "status": "success",
        "report": _last_refinement_report.get_summary(),
        "detailed_changes": _get_detailed_refinement_changes()
    }


def _get_detailed_refinement_changes() -> Dict[str, Any]:
    """Get detailed changes from the last refinement report."""
    global _last_refinement_report
    
    if _last_refinement_report is None:
        return {}
    
    changes = {
        "step_histories": {},
        "removed_tools": [],
        "parameter_adjustments": [],
        "iteration_artifacts": {}
    }
    
    for step_id, history in _last_refinement_report.step_histories.items():
        step_info = {
            "step_name": history.step_name,
            "tool_id": history.tool_id,
            "total_iterations": history.total_iterations,
            "final_iteration": history.final_iteration,
            "was_removed": history.was_removed,
            "removal_reason": history.removal_reason,
            "locked_parameters": history.user_locked_params,
            "iteration_details": []
        }
        
        step_artifacts = {}
        
        for iteration in history.iterations:
            iter_detail = {
                "iteration": iteration.iteration,
                "inputs": iteration.inputs_used,
                "duration_seconds": iteration.duration_seconds,
            }
            
            if "_iteration_artifacts" in iteration.outputs:
                iter_detail["artifacts"] = iteration.outputs["_iteration_artifacts"]
                step_artifacts[iteration.iteration] = iteration.outputs["_iteration_artifacts"]
            
            if iteration.decision:
                iter_detail["decision"] = {
                    "quality": iteration.decision.quality_score.value,
                    "action": iteration.decision.action.value,
                    "assessment": iteration.decision.assessment,
                    "reasoning": iteration.decision.reasoning,
                }
                
                if iteration.decision.parameter_changes:
                    iter_detail["parameter_changes"] = [
                        {
                            "param": c.parameter_name,
                            "from": c.old_value,
                            "to": c.new_value,
                            "reason": c.reason
                        }
                        for c in iteration.decision.parameter_changes
                    ]
                    
                    for c in iteration.decision.parameter_changes:
                        changes["parameter_adjustments"].append({
                            "step": history.step_name,
                            "param": c.parameter_name,
                            "from": c.old_value,
                            "to": c.new_value,
                            "reason": c.reason
                        })
            
            step_info["iteration_details"].append(iter_detail)
        
        changes["step_histories"][step_id] = step_info
        
        if step_artifacts:
            changes["iteration_artifacts"][history.step_name] = {
                "step_id": step_id,
                "iterations": step_artifacts,
                "final_iteration": history.final_iteration
            }
        
        if history.was_removed:
            changes["removed_tools"].append({
                "step": history.step_name,
                "tool": history.tool_id,
                "reason": history.removal_reason
            })
    
    return changes


def get_iteration_artifacts(step_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get paths to all iteration images/artifacts from the last adaptive execution.
    
    This allows you to see the output from each iteration of each step,
    not just the final result. Useful for understanding how the refinement
    process worked and comparing different parameter settings.
    
    Args:
        step_name: Optional step name to filter by
        
    Returns:
        Dictionary with iteration artifact paths organized by step
    """
    global _last_refinement_report
    
    if _last_refinement_report is None:
        return {
            "status": "error",
            "message": "No refinement report available. Run execute_pipeline_adaptive first."
        }
    
    artifacts = {
        "status": "success",
        "steps": {}
    }
    
    for step_id, history in _last_refinement_report.step_histories.items():
        if step_name and history.step_name != step_name:
            continue
        
        step_info = {
            "step_name": history.step_name,
            "tool": history.tool_id,
            "total_iterations": history.total_iterations,
            "final_iteration": history.final_iteration,
            "iterations": {}
        }
        
        for iteration in history.iterations:
            iter_artifacts = {}
            
            if "_iteration_artifacts" in iteration.outputs:
                iter_artifacts = iteration.outputs["_iteration_artifacts"]
            
            for key, value in iteration.outputs.items():
                if key != "_iteration_artifacts" and isinstance(value, str):
                    if any(value.lower().endswith(ext) for ext in 
                           ['.png', '.jpg', '.jpeg', '.tif', '.tiff']):
                        iter_artifacts[f"original_{key}"] = value
            
            if iter_artifacts:
                step_info["iterations"][iteration.iteration] = {
                    "artifacts": iter_artifacts,
                    "inputs_used": iteration.inputs_used,
                    "is_final": iteration.iteration == history.final_iteration
                }
        
        if step_info["iterations"]:
            artifacts["steps"][history.step_name] = step_info
    
    return artifacts


def get_results(step_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get execution results.
    
    Args:
        step_name: Optional step name to get specific results
        
    Returns:
        Results for the step or all steps
    """
    manager = _get_manager()
    session = _get_session()
    
    if not manager.current_pipeline:
        return {"status": "error", "message": "No active pipeline"}
    
    results = session.get_result(manager.current_pipeline.pipeline_id)
    
    if not results:
        return {"status": "error", "message": "No results found"}
    
    if step_name:
        for sr in results.get("step_results", []):
            if sr["step_name"] == step_name:
                return sr
        return {"status": "error", "message": f"Step not found: {step_name}"}
    
    return results


def get_pipeline_summary() -> Dict[str, Any]:
    """
    Get a summary of the current pipeline.
    
    Returns:
        Pipeline summary with all steps and connections
    """
    manager = _get_manager()
    return manager.get_pipeline_summary()


def save_pipeline(name: str, description: str = "") -> Dict[str, Any]:
    """
    Save the current pipeline as a reusable template.
    
    Args:
        name: Template name (must be unique)
        description: Description of the pipeline
        
    Returns:
        Save status
    """
    manager = _get_manager()
    session = _get_session()
    
    if not manager.current_pipeline:
        return {"status": "error", "message": "No active pipeline"}
    
    try:
        template_id = session.save_as_template(
            manager.current_pipeline,
            name=name,
            description=description
        )
        return {
            "status": "saved",
            "template_name": name,
            "template_id": template_id,
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def load_pipeline(name: str) -> Dict[str, Any]:
    """
    Load a saved pipeline template.
    
    Args:
        name: Template name
        
    Returns:
        Pipeline summary
    """
    manager = _get_manager()
    session = _get_session()
    
    pipeline = session.load_template(name)
    if not pipeline:
        return {"status": "error", "message": f"Template not found: {name}"}
    
    manager.load_pipeline(pipeline)
    return {
        "status": "loaded",
        "pipeline_id": pipeline.pipeline_id,
        "name": pipeline.name,
        "steps_count": len(pipeline.steps),
    }


def list_saved_pipelines(category: Optional[str] = None) -> Dict[str, Any]:
    """
    List saved pipeline templates.
    
    Args:
        category: Optional category filter
        
    Returns:
        List of templates
    """
    session = _get_session()
    templates = session.list_templates(category=category)
    
    return {
        "templates": templates,
        "total_count": len(templates),
    }


def export_pipeline() -> str:
    """
    Export the current pipeline as JSON.
    
    Returns:
        JSON string of the pipeline definition
    """
    manager = _get_manager()
    
    if not manager.current_pipeline:
        return '{"error": "No active pipeline"}'
    
    return manager.to_json()


def import_pipeline(json_str: str) -> Dict[str, Any]:
    """
    Import a pipeline from JSON.

    Args:
        json_str: JSON pipeline definition

    Returns:
        Import status
    """
    global _current_manager

    try:
        _current_manager = PipelineManager.from_json(json_str)
        pipeline = _current_manager.current_pipeline
        return {
            "status": "imported",
            "pipeline_id": pipeline.pipeline_id,
            "name": pipeline.name,
            "steps_count": len(pipeline.steps),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_current_pipeline_for_frontend() -> Optional[Dict[str, Any]]:
    """
    Get the current pipeline in frontend-compatible format.

    This converts the backend Pipeline structure to the format expected
    by the frontend visual pipeline editor.

    Returns:
        Pipeline in frontend format, or None if no pipeline exists
    """
    manager = _get_manager()

    if not manager.current_pipeline:
        return None

    pipeline = manager.current_pipeline
    registry = get_registry()

    nodes = []
    step_id_to_node_id = {}

    x_position = 250
    y_position = 50
    y_spacing = 180

    for idx, step in enumerate(pipeline.steps):
        node_id = f"node_{step.step_id}"
        step_id_to_node_id[step.step_id] = node_id

        schema = registry.get_schema(step.tool_id)
        if not schema:
            continue

        def build_input_def(inp):
            """Build input definition with optional constraints."""
            input_def = {
                "name": inp.name,
                "type": inp.type.value.upper(),
                "description": inp.description or "",
                "required": inp.required,
                "default": inp.default,
            }
            constraints = {}
            if inp.min_value is not None:
                constraints["min_value"] = inp.min_value
            if inp.max_value is not None:
                constraints["max_value"] = inp.max_value
            if inp.choices is not None:
                constraints["choices"] = inp.choices
            if constraints:
                input_def["constraints"] = constraints
            return input_def

        filtered_inputs = [
            inp for inp in schema.inputs
            if not (inp.name == "output_path" and schema.tool_id != "save_image")
        ]

        tool_def = {
            "id": schema.tool_id,
            "name": schema.name,
            "description": schema.description,
            "category": schema.category,
            "inputs": [build_input_def(inp) for inp in filtered_inputs],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type.value.upper(),
                    "description": out.description or "",
                }
                for out in schema.outputs
            ],
        }

        inputs = {}
        for input_name, step_input in step.inputs.items():
            if step_input.source == InputSource.STATIC:
                inputs[input_name] = {
                    "type": "static",
                    "value": step_input.value,
                }
            elif step_input.source == InputSource.STEP_OUTPUT:
                source_node_id = step_id_to_node_id.get(step_input.source_step_id, "")
                inputs[input_name] = {
                    "type": "connection",
                    "sourceNodeId": source_node_id,
                    "sourceOutput": step_input.source_output,
                }
            elif step_input.source == InputSource.USER_INPUT:
                inputs[input_name] = {
                    "type": "user_input",
                    "value": step_input.value,
                }

        node = {
            "id": node_id,
            "toolId": step.tool_id,
            "tool": tool_def,
            "position": {"x": x_position, "y": y_position + idx * y_spacing},
            "inputs": inputs,
        }
        nodes.append(node)

    edges = []
    edge_idx = 0
    for step in pipeline.steps:
        target_node_id = step_id_to_node_id.get(step.step_id)
        if not target_node_id:
            continue

        for input_name, step_input in step.inputs.items():
            if step_input.source == InputSource.STEP_OUTPUT and step_input.source_step_id:
                source_node_id = step_id_to_node_id.get(step_input.source_step_id)
                if source_node_id:
                    edge = {
                        "id": f"edge_{edge_idx}",
                        "sourceNodeId": source_node_id,
                        "sourceOutput": step_input.source_output,
                        "targetNodeId": target_node_id,
                        "targetInput": input_name,
                    }
                    edges.append(edge)
                    edge_idx += 1

    return {
        "id": pipeline.pipeline_id,
        "name": pipeline.name,
        "description": pipeline.description or "",
        "nodes": nodes,
        "edges": edges,
    }


def has_current_pipeline() -> bool:
    """Check if there's an active pipeline."""
    manager = _get_manager()
    return manager.current_pipeline is not None and len(manager.current_pipeline.steps) > 0
