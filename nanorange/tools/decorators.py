"""
Decorators for easy tool creation and registration.

The @tool decorator allows you to turn any function into a NanoRange tool
with automatic schema generation from type hints and docstrings.
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, get_type_hints
from nanorange.core.schemas import (
    DataType,
    InputSchema,
    OutputSchema,
    ToolSchema,
    ToolType,
)
from nanorange.core.registry import get_registry


# Mapping from Python types to DataType
TYPE_MAPPING = {
    str: DataType.STRING,
    int: DataType.INT,
    float: DataType.FLOAT,
    bool: DataType.BOOL,
    list: DataType.LIST,
    dict: DataType.DICT,
}


def _get_data_type(python_type: Type) -> DataType:
    """Convert Python type to DataType."""
    # Handle Optional types
    origin = getattr(python_type, "__origin__", None)
    if origin is type(None):
        return DataType.STRING  # Default for None
    
    # Check for List, Dict etc
    if origin is list:
        return DataType.LIST
    if origin is dict:
        return DataType.DICT
    
    # Direct mapping
    return TYPE_MAPPING.get(python_type, DataType.STRING)


def _parse_docstring(docstring: Optional[str]) -> Dict[str, str]:
    """
    Parse docstring to extract parameter descriptions.
    
    Supports Google-style docstrings:
        Args:
            param_name: Description of the parameter.
            
    Returns:
        Dictionary mapping parameter names to descriptions.
    """
    if not docstring:
        return {}
    
    descriptions = {}
    in_args_section = False
    current_param = None
    current_desc = []
    
    for line in docstring.split("\n"):
        stripped = line.strip()
        
        if stripped.lower().startswith("args:"):
            in_args_section = True
            continue
        elif stripped.lower().startswith(("returns:", "raises:", "example:")):
            in_args_section = False
            if current_param:
                descriptions[current_param] = " ".join(current_desc).strip()
            current_param = None
            continue
        
        if in_args_section and stripped:
            # Check if this is a new parameter
            if ":" in stripped and not stripped.startswith(" "):
                if current_param:
                    descriptions[current_param] = " ".join(current_desc).strip()
                
                parts = stripped.split(":", 1)
                current_param = parts[0].strip()
                current_desc = [parts[1].strip()] if len(parts) > 1 else []
            elif current_param:
                # Continuation of previous parameter description
                current_desc.append(stripped)
    
    # Don't forget the last parameter
    if current_param:
        descriptions[current_param] = " ".join(current_desc).strip()
    
    return descriptions


def tool(
    tool_id: Optional[str] = None,
    name: Optional[str] = None,
    category: str = "general",
    tags: Optional[List[str]] = None,
    output_type: DataType = DataType.STRING,
    output_name: str = "result",
    output_description: str = "",
    register: bool = True,
    **extra_outputs
):
    """
    Decorator to create a tool from a function.
    
    The decorator automatically generates input schemas from function
    signature and type hints, and output schema from decorator arguments.
    
    Args:
        tool_id: Unique tool identifier (defaults to function name)
        name: Human-readable name (defaults to function name with spaces)
        category: Tool category for organization
        tags: Searchable tags
        output_type: Type of the main output
        output_name: Name of the main output
        output_description: Description of the main output
        register: Whether to auto-register with global registry
        **extra_outputs: Additional outputs as name=DataType pairs
        
    Example:
        @tool(
            tool_id="gaussian_blur",
            name="Gaussian Blur",
            category="preprocessing",
            output_type=DataType.IMAGE,
            output_name="blurred_image",
        )
        def gaussian_blur(image_path: str, sigma: float = 1.0) -> str:
            '''Apply Gaussian blur to an image.
            
            Args:
                image_path: Path to the input image.
                sigma: Standard deviation for the Gaussian kernel.
            '''
            # Implementation
            return output_path
    """
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        func_name = func.__name__
        sig = inspect.signature(func)
        hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
        docstring = func.__doc__ or ""
        param_descriptions = _parse_docstring(docstring)
        
        # Generate tool ID and name
        actual_tool_id = tool_id or func_name
        actual_name = name or func_name.replace("_", " ").title()
        
        # Extract first line of docstring as description
        description = docstring.split("\n")[0].strip() if docstring else ""
        
        # Generate input schemas from signature
        inputs = []
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            
            # Determine type
            param_type = hints.get(param_name, str)
            data_type = _get_data_type(param_type)
            
            # Check for special type hints in parameter name
            if "image" in param_name.lower() or "path" in param_name.lower():
                if "image" in param_name.lower():
                    data_type = DataType.IMAGE
                elif "mask" in param_name.lower():
                    data_type = DataType.MASK
            
            # Determine if required and default value
            required = param.default is inspect.Parameter.empty
            default = None if required else param.default
            
            inputs.append(InputSchema(
                name=param_name,
                type=data_type,
                description=param_descriptions.get(param_name, ""),
                required=required,
                default=default,
            ))
        
        # Generate output schemas
        outputs = [OutputSchema(
            name=output_name,
            type=output_type,
            description=output_description,
        )]
        
        # Add extra outputs
        for out_name, out_type in extra_outputs.items():
            if isinstance(out_type, DataType):
                outputs.append(OutputSchema(
                    name=out_name,
                    type=out_type,
                    description="",
                ))
        
        # Create schema
        schema = ToolSchema(
            tool_id=actual_tool_id,
            name=actual_name,
            description=description,
            type=ToolType.FUNCTION,
            category=category,
            inputs=inputs,
            outputs=outputs,
            tags=tags or [],
        )
        
        # Wrap the function to return dict with output name
        @wraps(func)
        def wrapper(**kwargs) -> Dict[str, Any]:
            result = func(**kwargs)
            
            # If function returns a dict, assume it's already formatted
            if isinstance(result, dict):
                return result
            
            # Otherwise, wrap in dict with output name
            return {output_name: result}
        
        # Attach schema to wrapper
        wrapper._tool_schema = schema
        wrapper._original_func = func
        
        # Register with global registry
        if register:
            registry = get_registry()
            if not registry.has_tool(actual_tool_id):
                registry.register(schema, wrapper)
        
        return wrapper
    
    return decorator


def agent_tool(
    tool_id: Optional[str] = None,
    name: Optional[str] = None,
    category: str = "ai",
    tags: Optional[List[str]] = None,
    register: bool = True,
):
    """
    Decorator for agent-based tools.
    
    Similar to @tool but marks the tool as an agent type.
    The decorated function should be an async function that
    interacts with a sub-agent.
    
    Example:
        @agent_tool(
            tool_id="ai_enhancer",
            name="AI Image Enhancer",
            category="enhancement",
        )
        async def ai_enhance(image_path: str, instructions: str) -> Dict[str, Any]:
            '''Enhance image using Gemini 3.0.
            
            Args:
                image_path: Path to input image.
                instructions: Enhancement instructions.
            '''
            # Implementation with sub-agent
            return {"enhanced_image": output_path}
    """
    def decorator(func: Callable) -> Callable:
        # First apply the basic tool decorator logic
        func_name = func.__name__
        actual_tool_id = tool_id or func_name
        
        # Use the tool decorator for schema generation
        tool_wrapper = tool(
            tool_id=actual_tool_id,
            name=name,
            category=category,
            tags=tags,
            register=False,  # We'll register manually with agent type
        )(func)
        
        # Modify schema to be agent type
        schema = tool_wrapper._tool_schema
        schema.type = ToolType.AGENT
        
        # Register with global registry
        if register:
            registry = get_registry()
            if not registry.has_tool(actual_tool_id):
                registry.register(schema, tool_wrapper)
        
        return tool_wrapper
    
    return decorator


def get_tool_schema(func: Callable) -> Optional[ToolSchema]:
    """Get the schema attached to a decorated function."""
    return getattr(func, "_tool_schema", None)
