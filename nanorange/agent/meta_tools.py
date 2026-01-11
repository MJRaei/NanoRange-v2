"""
Meta-tools for pipeline manipulation.

These tools are used by the orchestrator agent to:
- Discover available tools
- Build and modify pipelines
- Execute and validate pipelines
- Save and load pipeline templates
"""

from typing import Any, Dict, List, Optional
from nanorange.core.schemas import Pipeline, PipelineStep, StepInput
from nanorange.core.registry import get_registry
from nanorange.core.pipeline import PipelineManager
from nanorange.core.executor import PipelineExecutor
from nanorange.storage.session_manager import SessionManager


# Global state for the current session
_current_manager: Optional[PipelineManager] = None
_current_session: Optional[SessionManager] = None
_current_executor: Optional[PipelineExecutor] = None


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
        _current_executor = PipelineExecutor()
    return _current_executor


def initialize_session(session_id: Optional[str] = None) -> str:
    """
    Initialize or resume a session.
    
    Args:
        session_id: Optional existing session ID to resume
        
    Returns:
        The session ID
    """
    global _current_session, _current_manager
    
    # Discover and register built-in tools
    registry = get_registry()
    registry.discover_tools()
    
    if session_id:
        _current_session = SessionManager(session_id=session_id)
    else:
        _current_session = SessionManager()
        _current_session.create_session()
    
    _current_manager = PipelineManager()
    return _current_session.session_id


# ============================================================================
# Tool Discovery
# ============================================================================

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
        "inputs": [inp.model_dump() for inp in schema.inputs],
        "outputs": [out.model_dump() for out in schema.outputs],
    }


# ============================================================================
# Pipeline Building
# ============================================================================

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


# ============================================================================
# Pipeline Validation & Execution
# ============================================================================

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
    
    # Validate first
    validation = manager.validate()
    if not validation.is_valid:
        return {
            "status": "validation_failed",
            "errors": [str(e) for e in validation.errors],
        }
    
    # Execute
    result = executor.execute(
        manager.current_pipeline,
        user_inputs=user_inputs,
        stop_on_error=stop_on_error
    )
    
    # Save result to session
    session = _get_session()
    session.save_pipeline(manager.current_pipeline)
    session.save_result(result)
    
    # Format response
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


# ============================================================================
# Pipeline Persistence
# ============================================================================

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
