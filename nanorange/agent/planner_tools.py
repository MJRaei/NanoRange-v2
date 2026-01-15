"""
Tools for the Planner Agent.

These tools help the planner:
- Discover available analysis tools
- Create and propose pipeline plans
- Get user approval before execution
"""

from typing import Any, Dict, List, Optional
from nanorange.core.registry import get_registry


def list_tools_for_planning(category: Optional[str] = None) -> Dict[str, Any]:
    """
    List available tools for pipeline planning.
    
    Use this to discover what tools are available and their capabilities
    when designing a pipeline for the user's request.
    
    Args:
        category: Optional category filter (io, preprocessing, segmentation, 
                  measurement, vlm)
    
    Returns:
        Dictionary with tools organized by category, including their
        inputs, outputs, and descriptions.
    """
    registry = get_registry()
    registry.discover_tools()
    
    tools = registry.list_tools(category=category)
    
    # Organize by category for easier planning
    by_category: Dict[str, List[Dict]] = {}
    
    for tool in tools:
        cat = tool.category
        if cat not in by_category:
            by_category[cat] = []
        
        by_category[cat].append({
            "tool_id": tool.tool_id,
            "name": tool.name,
            "description": tool.description,
            "type": tool.type.value,
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type.value,
                    "required": inp.required,
                    "default": inp.default,
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
        "categories": list(by_category.keys()),
        "tools_by_category": by_category,
        "total_tools": len(tools),
    }


def create_pipeline_plan(
    name: str,
    description: str,
    steps: List[Dict[str, Any]],
    reasoning: str
) -> Dict[str, Any]:
    """
    Create a pipeline plan to present to the user.
    
    Use this to propose a pipeline after analyzing the user's request.
    The plan will be shown to the user for approval before execution.
    
    Args:
        name: Short name for the pipeline (e.g., "Cell Segmentation Pipeline")
        description: What this pipeline does and why these steps were chosen
        steps: List of pipeline steps, each with:
            - step_name: Human-readable name
            - tool_id: The tool to use
            - inputs: Dict of input parameters and their values/sources
            - purpose: Why this step is needed
        reasoning: Explanation of why this pipeline design was chosen
        
    Returns:
        Formatted plan for user review
        
    Example steps format:
        [
            {
                "step_name": "Load Image",
                "tool_id": "load_image",
                "inputs": {"image_path": "<user_provided>"},
                "purpose": "Load the input microscopy image"
            },
            {
                "step_name": "Enhance Contrast", 
                "tool_id": "ai_enhance_image",
                "inputs": {
                    "image_path": "<from: Load Image.image>",
                    "background_color": "black",
                    "foreground_color": "white"
                },
                "purpose": "Clean up image and enhance object boundaries"
            }
        ]
    """
    # Format the plan for display
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        formatted_step = {
            "order": i,
            "name": step.get("step_name", f"Step {i}"),
            "tool": step.get("tool_id"),
            "inputs": step.get("inputs", {}),
            "purpose": step.get("purpose", ""),
        }
        formatted_steps.append(formatted_step)
    
    plan = {
        "plan_name": name,
        "description": description,
        "steps": formatted_steps,
        "total_steps": len(steps),
        "reasoning": reasoning,
        "status": "pending_approval",
        "message": (
            "I've created this pipeline plan based on your request. "
            "Please review the steps and let me know if you'd like to:\n"
            "1. **Approve** - Execute this pipeline as planned\n"
            "2. **Modify** - Change specific steps or parameters\n"
            "3. **Reject** - Start over with different approach"
        ),
    }
    
    return plan


def analyze_image_for_planning(image_path: str) -> Dict[str, Any]:
    """
    Analyze an image to help plan the appropriate pipeline.
    
    Use this when the user provides an image to understand:
    - Image type (fluorescence, brightfield, etc.)
    - Objects present (cells, particles, structures)
    - Image quality (noise level, contrast)
    - Recommended preprocessing steps
    
    Args:
        image_path: Path to the image to analyze
        
    Returns:
        Analysis results to inform pipeline planning
    """
    from pathlib import Path
    from PIL import Image
    import numpy as np
    
    path = Path(image_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"Image not found: {image_path}",
        }
    
    try:
        img = Image.open(path)
        arr = np.array(img)
        
        # Basic image analysis
        analysis = {
            "success": True,
            "image_path": str(path.absolute()),
            "filename": path.name,
            "dimensions": {
                "width": img.width,
                "height": img.height,
            },
            "mode": img.mode,
            "channels": len(img.getbands()),
            "format": img.format,
        }
        
        # Intensity statistics
        if arr.ndim == 2:  # Grayscale
            analysis["intensity"] = {
                "min": int(arr.min()),
                "max": int(arr.max()),
                "mean": float(arr.mean()),
                "std": float(arr.std()),
            }
            analysis["is_grayscale"] = True
        else:
            analysis["is_grayscale"] = False
            if arr.ndim == 3:
                analysis["intensity"] = {
                    "min": int(arr.min()),
                    "max": int(arr.max()),
                    "mean": float(arr.mean()),
                }
        
        # Quality indicators
        if "intensity" in analysis:
            intensity = analysis["intensity"]
            dynamic_range = intensity["max"] - intensity["min"]
            analysis["quality_hints"] = {
                "dynamic_range": dynamic_range,
                "low_contrast": dynamic_range < 50,
                "high_noise_likely": intensity.get("std", 0) > 60,
                "needs_normalization": intensity["max"] < 200 or intensity["min"] > 50,
            }
        
        analysis["recommendations"] = []
        if analysis.get("quality_hints", {}).get("low_contrast"):
            analysis["recommendations"].append("Consider contrast enhancement or normalization")
        if analysis.get("quality_hints", {}).get("high_noise_likely"):
            analysis["recommendations"].append("Consider noise reduction (gaussian blur or AI enhancement)")
        
        return analysis
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def get_tool_compatibility(from_tool_id: str, to_tool_id: str) -> Dict[str, Any]:
    """
    Check if two tools can be connected in a pipeline.
    
    Use this to verify that outputs from one tool can be used as
    inputs to another tool.
    
    Args:
        from_tool_id: Source tool ID
        to_tool_id: Target tool ID
        
    Returns:
        Compatible connections between the tools
    """
    registry = get_registry()
    
    from_schema = registry.get_schema(from_tool_id)
    to_schema = registry.get_schema(to_tool_id)
    
    if not from_schema:
        return {"error": f"Tool not found: {from_tool_id}"}
    if not to_schema:
        return {"error": f"Tool not found: {to_tool_id}"}
    
    # Find compatible output->input pairs
    compatible = []
    for output in from_schema.outputs:
        for inp in to_schema.inputs:
            # Check type compatibility
            if output.type == inp.type:
                compatible.append({
                    "from_output": output.name,
                    "to_input": inp.name,
                    "type": output.type.value,
                    "required": inp.required,
                })
            # Check for compatible types (e.g., image -> path)
            elif output.type.value in ["image", "mask", "path"] and inp.type.value in ["image", "mask", "path"]:
                compatible.append({
                    "from_output": output.name,
                    "to_input": inp.name,
                    "from_type": output.type.value,
                    "to_type": inp.type.value,
                    "required": inp.required,
                })
    
    return {
        "from_tool": from_tool_id,
        "to_tool": to_tool_id,
        "compatible_connections": compatible,
        "can_connect": len(compatible) > 0,
    }
