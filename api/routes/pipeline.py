"""
Pipeline API Routes

Handles pipeline-related API requests including tool listing,
pipeline execution, and pipeline persistence.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from nanorange.core.registry import get_registry
from nanorange.core.schemas import ToolSchema, InputSchema, OutputSchema, DataType
from nanorange.core.executor import PipelineExecutor
from nanorange.core.pipeline import Pipeline, PipelineStep
from nanorange.core.schemas import StepInput, InputSource, StepStatus

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Directory for storing saved pipelines
PIPELINES_DIR = "data/pipelines"

# In-memory storage for pipeline executions (can upgrade to Redis later)
pipeline_executions: Dict[str, Any] = {}
execution_lock = asyncio.Lock()


# ============================================================================
# Request/Response Models
# ============================================================================

class ToolSchemaResponse(BaseModel):
    """Tool schema in frontend-compatible format."""
    id: str
    name: str
    description: str
    category: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]


class ToolListResponse(BaseModel):
    """Response containing list of available tools."""
    tools: List[ToolSchemaResponse]
    categories: List[str]


class PipelineExecuteRequest(BaseModel):
    """Request to execute a pipeline."""
    pipeline: Dict[str, Any]  # Frontend pipeline structure
    session_id: Optional[str] = None
    user_inputs: Optional[Dict[str, Dict[str, Any]]] = None


class PipelineExecuteResponse(BaseModel):
    """Response from pipeline execution request."""
    execution_id: str
    status: str  # "queued" | "running" | "completed" | "failed"
    message: Optional[str] = None


class ExecutionStatusResponse(BaseModel):
    """Status of a pipeline execution."""
    execution_id: str
    status: str  # "running" | "completed" | "failed"
    progress: float  # 0.0 to 1.0
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PipelineSaveRequest(BaseModel):
    """Request to save a pipeline."""
    pipeline: Dict[str, Any]
    name: str
    description: Optional[str] = None


class PipelineSaveResponse(BaseModel):
    """Response from saving a pipeline."""
    pipeline_id: str
    saved_at: datetime


class PipelineSummary(BaseModel):
    """Summary information about a saved pipeline."""
    pipeline_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    modified_at: datetime
    step_count: int


class SavedPipelinesResponse(BaseModel):
    """List of saved pipelines."""
    pipelines: List[PipelineSummary]


# ============================================================================
# Transformation Functions
# ============================================================================

def backend_tool_to_frontend(tool_schema: ToolSchema) -> ToolSchemaResponse:
    """
    Convert backend ToolSchema to frontend format.

    Args:
        tool_schema: Backend tool schema

    Returns:
        Frontend-compatible tool schema
    """
    return ToolSchemaResponse(
        id=tool_schema.tool_id,
        name=tool_schema.name,
        description=tool_schema.description,
        category=tool_schema.category,
        inputs=[
            {
                "name": inp.name,
                "type": inp.type.value.upper(),  # IMAGE -> "IMAGE"
                "description": inp.description,
                "required": inp.required,
                "default": inp.default,
                "constraints": {
                    k: v for k, v in {
                        "min_value": inp.min_value,
                        "max_value": inp.max_value,
                        "choices": inp.choices,
                    }.items() if v is not None
                } if inp.min_value or inp.max_value or inp.choices else None
            }
            for inp in tool_schema.inputs
        ],
        outputs=[
            {
                "name": out.name,
                "type": out.type.value.upper(),  # IMAGE -> "IMAGE"
                "description": out.description,
            }
            for out in tool_schema.outputs
        ],
    )


def frontend_pipeline_to_backend(frontend_pipeline: dict) -> Pipeline:
    """
    Transform frontend pipeline structure to backend Pipeline schema.

    Frontend structure:
    {
      "id": "...",
      "name": "...",
      "nodes": [
        {
          "id": "node_1",
          "toolId": "load_image",
          "tool": {...},
          "position": {"x": 100, "y": 100},
          "inputs": {
            "image_path": {
              "type": "static",
              "value": "/path/to/image.png"
            }
          }
        }
      ],
      "edges": [
        {
          "id": "edge_1",
          "sourceNodeId": "node_1",
          "sourceOutput": "image",
          "targetNodeId": "node_2",
          "targetInput": "input_image"
        }
      ]
    }

    Args:
        frontend_pipeline: Pipeline structure from frontend

    Returns:
        Backend Pipeline object
    """
    registry = get_registry()

    # Extract pipeline metadata
    pipeline_id = frontend_pipeline.get("id", str(uuid.uuid4()))
    name = frontend_pipeline.get("name", "Untitled Pipeline")
    description = frontend_pipeline.get("description", "")
    nodes = frontend_pipeline.get("nodes", [])
    edges = frontend_pipeline.get("edges", [])

    # Create a mapping of edges by target node and input
    edge_map: Dict[str, Dict[str, dict]] = {}
    for edge in edges:
        target_node_id = edge["targetNodeId"]
        target_input = edge["targetInput"]
        if target_node_id not in edge_map:
            edge_map[target_node_id] = {}
        edge_map[target_node_id][target_input] = edge

    # Convert nodes to pipeline steps
    steps = []
    for node in nodes:
        node_id = node["id"]
        tool_id = node["toolId"]
        tool_schema = registry.get_schema(tool_id)

        if not tool_schema:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{tool_id}' not found in registry"
            )

        # Build step inputs
        step_inputs = {}
        node_inputs = node.get("inputs", {})

        for input_schema in tool_schema.inputs:
            input_name = input_schema.name

            # Check if this input is connected via an edge
            if node_id in edge_map and input_name in edge_map[node_id]:
                edge = edge_map[node_id][input_name]
                step_inputs[input_name] = StepInput(
                    source=InputSource.STEP_OUTPUT,
                    source_step_id=edge["sourceNodeId"],
                    source_output=edge["sourceOutput"]
                )
            # Check if there's a static value or user input
            elif input_name in node_inputs:
                node_input = node_inputs[input_name]
                input_type = node_input.get("type", "static")

                if input_type == "connection":
                    # This should have been handled by edges, but check anyway
                    if "sourceNodeId" in node_input:
                        step_inputs[input_name] = StepInput(
                            source=InputSource.STEP_OUTPUT,
                            source_step_id=node_input["sourceNodeId"],
                            source_output=node_input.get("sourceOutput", "")
                        )
                elif input_type == "user_input":
                    step_inputs[input_name] = StepInput(
                        source=InputSource.USER_INPUT,
                        prompt=node_input.get("prompt", f"Enter {input_name}")
                    )
                else:  # static
                    step_inputs[input_name] = StepInput(
                        source=InputSource.STATIC,
                        value=node_input.get("value")
                    )
            # Use default value if available
            elif input_schema.default is not None:
                step_inputs[input_name] = StepInput(
                    source=InputSource.STATIC,
                    value=input_schema.default
                )
            # Required input with no value
            elif input_schema.required:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required input '{input_name}' missing for tool '{tool_id}' in node '{node_id}'"
                )

        # Create pipeline step
        step = PipelineStep(
            step_id=node_id,
            step_name=tool_schema.name,
            tool_id=tool_id,
            inputs=step_inputs,
            status=StepStatus.PENDING
        )
        steps.append(step)

    # Create and return pipeline
    return Pipeline(
        pipeline_id=pipeline_id,
        name=name,
        description=description,
        steps=steps,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/tools", response_model=ToolListResponse)
async def list_tools(category: Optional[str] = None):
    """
    List all available tools.

    Args:
        category: Optional filter by category

    Returns:
        List of tools with their schemas and available categories
    """
    try:
        registry = get_registry()

        # Get tools (filtered by category if specified)
        tool_schemas = registry.list_tools(category=category)

        # Transform to frontend format
        tools = [backend_tool_to_frontend(schema) for schema in tool_schemas]

        # Get all categories
        categories = registry.list_categories()

        return ToolListResponse(
            tools=tools,
            categories=categories
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.post("/execute", response_model=PipelineExecuteResponse)
async def execute_pipeline(request: PipelineExecuteRequest):
    """
    Execute a pipeline.

    The pipeline is executed asynchronously. Use the execution_id
    to poll for status and results.

    Args:
        request: Pipeline execution request

    Returns:
        Execution ID for status polling
    """
    try:
        # Transform frontend pipeline to backend format
        pipeline = frontend_pipeline_to_backend(request.pipeline)

        # Generate execution ID
        execution_id = str(uuid.uuid4())

        # Store execution metadata
        async with execution_lock:
            pipeline_executions[execution_id] = {
                "pipeline": pipeline,
                "status": "running",
                "progress": 0.0,
                "current_step": None,
                "result": None,
                "error": None,
                "started_at": datetime.now(),
            }

        # Execute pipeline in background
        asyncio.create_task(_execute_pipeline_async(execution_id, pipeline))

        return PipelineExecuteResponse(
            execution_id=execution_id,
            status="running",
            message="Pipeline execution started"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline execution: {str(e)}"
        )


async def _execute_pipeline_async(execution_id: str, pipeline: Pipeline):
    """
    Execute pipeline asynchronously and update execution status.

    Args:
        execution_id: Execution identifier
        pipeline: Pipeline to execute
    """
    try:
        # Create executor
        executor = PipelineExecutor(registry=get_registry())

        # Execute pipeline
        result = executor.execute(pipeline)

        # Update execution with result
        async with execution_lock:
            if execution_id in pipeline_executions:
                pipeline_executions[execution_id].update({
                    "status": "completed" if result.status == StepStatus.COMPLETED else "failed",
                    "progress": 1.0,
                    "result": {
                        "step_results": [
                            {
                                "step_id": sr.step_id,
                                "step_name": sr.step_name,
                                "status": sr.status.value,
                                "outputs": sr.outputs,
                                "error_message": sr.error_message,
                            }
                            for sr in result.step_results
                        ],
                        "final_outputs": result.step_results[-1].outputs if result.step_results else {},
                        "total_duration_seconds": result.total_duration_seconds,
                    },
                    "completed_at": datetime.now(),
                })
    except Exception as e:
        import traceback
        traceback.print_exc()

        # Update execution with error
        async with execution_lock:
            if execution_id in pipeline_executions:
                pipeline_executions[execution_id].update({
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now(),
                })


@router.get("/execution/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """
    Get the status of a pipeline execution.

    Args:
        execution_id: Execution identifier

    Returns:
        Current execution status and results if completed
    """
    async with execution_lock:
        execution = pipeline_executions.get(execution_id)

    if not execution:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{execution_id}' not found"
        )

    return ExecutionStatusResponse(
        execution_id=execution_id,
        status=execution["status"],
        progress=execution["progress"],
        current_step=execution.get("current_step"),
        result=execution.get("result"),
        error=execution.get("error"),
    )


@router.post("/save", response_model=PipelineSaveResponse)
async def save_pipeline(request: PipelineSaveRequest):
    """
    Save a pipeline to disk.

    Pipelines are stored as JSON files in the data/pipelines directory.

    Args:
        request: Pipeline save request

    Returns:
        Pipeline ID and save timestamp
    """
    try:
        # Ensure pipelines directory exists
        os.makedirs(PIPELINES_DIR, exist_ok=True)

        # Generate pipeline ID if not provided
        pipeline_id = request.pipeline.get("id", str(uuid.uuid4()))

        # Add metadata
        now = datetime.now()
        pipeline_data = {
            **request.pipeline,
            "id": pipeline_id,
            "name": request.name,
            "description": request.description or "",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }

        # Save to file
        file_path = os.path.join(PIPELINES_DIR, f"{pipeline_id}.json")
        with open(file_path, "w") as f:
            json.dump(pipeline_data, f, indent=2)

        return PipelineSaveResponse(
            pipeline_id=pipeline_id,
            saved_at=now
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save pipeline: {str(e)}"
        )


@router.get("/saved", response_model=SavedPipelinesResponse)
async def list_saved_pipelines():
    """
    List all saved pipelines.

    Returns:
        List of pipeline summaries
    """
    try:
        # Ensure directory exists
        os.makedirs(PIPELINES_DIR, exist_ok=True)

        summaries = []

        # Read all pipeline files
        for filename in os.listdir(PIPELINES_DIR):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(PIPELINES_DIR, filename)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                summaries.append(PipelineSummary(
                    pipeline_id=data.get("id", filename.replace(".json", "")),
                    name=data.get("name", "Untitled"),
                    description=data.get("description"),
                    created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                    modified_at=datetime.fromisoformat(data.get("modified_at", datetime.now().isoformat())),
                    step_count=len(data.get("nodes", []))
                ))
            except Exception as e:
                print(f"Warning: Could not read pipeline {filename}: {e}")
                continue

        # Sort by modified date (newest first)
        summaries.sort(key=lambda x: x.modified_at, reverse=True)

        return SavedPipelinesResponse(pipelines=summaries)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list saved pipelines: {str(e)}"
        )


@router.get("/saved/{pipeline_id}")
async def load_pipeline(pipeline_id: str):
    """
    Load a saved pipeline.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Complete pipeline definition
    """
    try:
        file_path = os.path.join(PIPELINES_DIR, f"{pipeline_id}.json")

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline '{pipeline_id}' not found"
            )

        with open(file_path, "r") as f:
            pipeline_data = json.load(f)

        return pipeline_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load pipeline: {str(e)}"
        )


@router.delete("/saved/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """
    Delete a saved pipeline.

    Args:
        pipeline_id: Pipeline identifier

    Returns:
        Success message
    """
    try:
        file_path = os.path.join(PIPELINES_DIR, f"{pipeline_id}.json")

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline '{pipeline_id}' not found"
            )

        os.remove(file_path)

        return {"success": True, "message": f"Pipeline '{pipeline_id}' deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete pipeline: {str(e)}"
        )
