"""
Gemini-powered boundary colorization tool.

Uses Gemini's image generation capabilities to:
- Assign distinct colors to particle/object boundaries
- Differentiate overlapping or touching objects
- Create visual separation for analysis
"""

from pathlib import Path
from typing import Any, Dict, Optional

from nanorange.core.schemas import (
    DataType,
    InputSchema,
    OutputSchema,
    ToolSchema,
    ToolType,
)
from nanorange.settings import IMAGE_MODEL_COLORIZER
from nanorange.tools.builtin.vlm_tools.base_image_agent import BaseImageAgent


class BoundaryColorizerAgent(BaseImageAgent):
    """
    Gemini agent for boundary colorization.
    
    Assigns distinct colors to object boundaries for visual differentiation.
    """
    
    def __init__(self, model: Optional[str] = None) -> None:
        """
        Initialize the Boundary Colorizer Agent.
        
        Args:
            model: Gemini model to use (defaults to IMAGE_MODEL_COLORIZER)
        """
        super().__init__(
            model=model or IMAGE_MODEL_COLORIZER,
            instruction=None  # Will be provided at runtime
        )


def build_colorizer_instruction(
    boundary_color: str = "white",
    max_colors: int = 10,
    high_contrast: bool = True,
    preserve_interior: bool = True,
    additional_instructions: str = ""
) -> str:
    """
    Build a customized boundary colorization instruction prompt.
    
    Args:
        boundary_color: Current color of boundaries in the input image
        max_colors: Maximum number of colors to use
        high_contrast: Use high-contrast colors for adjacent objects
        preserve_interior: Keep object interiors unchanged
        additional_instructions: Any additional custom instructions
        
    Returns:
        Complete instruction string for the model
    """
    instructions = [
        f"The current image shows object/particle boundaries rendered in {boundary_color}.",
        "Recolor the boundary of each distinct object using a different color.",
        "",
        "Requirements:",
        "1. If objects overlap, touch, or share connected edges, their boundaries MUST be assigned different colors.",
        f"2. Use no more than {max_colors} total colors.",
        "3. Maintain consistent color assignment across the entire image (the same object must always use the same color).",
    ]
    
    if high_contrast:
        instructions.append(
            "4. For objects that are very close together, nested, or overlapping, "
            "choose the highest-contrast color combinations to ensure their boundaries "
            "remain clearly distinguishable."
        )
    
    if preserve_interior:
        instructions.append(
            "\nDo not alter the object interiors—only recolor the boundary lines."
        )
    
    if additional_instructions:
        instructions.append(f"\n{additional_instructions}")
    
    instructions.append("\nReturn ONLY the processed image with colorized boundaries.")
    
    return "\n".join(instructions)


def colorize_boundaries(
    image_path: str,
    boundary_color: str = "white",
    max_colors: int = 10,
    high_contrast: bool = True,
    preserve_interior: bool = True,
    custom_instructions: str = "",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Colorize object boundaries using Gemini 3.0-powered processing.
    
    Uses Gemini's image generation to assign distinct colors to each
    object's boundary, making it easier to differentiate overlapping
    or touching objects.
    
    Args:
        image_path: Path to the input image with boundaries
        boundary_color: Current color of boundaries (e.g., "white", "black")
        max_colors: Maximum number of colors to use (default: 10)
        high_contrast: Use high-contrast colors for adjacent objects
        preserve_interior: Keep object interiors unchanged
        custom_instructions: Additional custom instructions for the model
        output_path: Output path (auto-generated if not provided)
        
    Returns:
        Dictionary with:
        - colorized_image: Path to colorized image (or None if failed)
        - success: Whether processing succeeded
        - error: Error message if failed
        - token_usage: Token usage statistics
    """
    source = Path(image_path)
    
    if not source.exists():
        return {
            "colorized_image": None,
            "success": False,
            "error": f"Image not found: {image_path}",
            "token_usage": {},
        }
    
    # Generate output path if not provided
    if output_path is None:
        output_path = str(
            source.parent / f"{source.stem}_colorized{source.suffix}"
        )
    
    # Build instruction
    instruction = build_colorizer_instruction(
        boundary_color=boundary_color,
        max_colors=max_colors,
        high_contrast=high_contrast,
        preserve_interior=preserve_interior,
        additional_instructions=custom_instructions,
    )
    
    # Create agent and process
    agent = BoundaryColorizerAgent()
    result = agent.process_image(
        input_path=image_path,
        output_path=output_path,
        instruction=instruction,
    )
    
    return {
        "colorized_image": result.get("output_path"),
        "success": result.get("success", False),
        "error": result.get("error"),
        "token_usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        },
    }


# Tool Schema Definition
COLORIZE_BOUNDARIES_SCHEMA = ToolSchema(
    tool_id="colorize_boundaries",
    name="Boundary Colorizer",
    description=(
        "Colorize object boundaries using Gemini 3.0. Assigns distinct colors to each "
        "object's boundary, making it easier to differentiate overlapping or "
        "touching particles/objects. Useful for segmentation visualization."
    ),
    type=ToolType.AGENT,
    category="vlm",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to the input image with object boundaries",
            required=True,
        ),
        InputSchema(
            name="boundary_color",
            type=DataType.STRING,
            description="Current color of boundaries in the input (e.g., 'white', 'black')",
            required=False,
            default="white",
        ),
        InputSchema(
            name="max_colors",
            type=DataType.INT,
            description="Maximum number of colors to use for boundaries",
            required=False,
            default=10,
            min_value=2,
            max_value=20,
        ),
        InputSchema(
            name="high_contrast",
            type=DataType.BOOL,
            description="Use high-contrast colors for adjacent objects",
            required=False,
            default=True,
        ),
        InputSchema(
            name="preserve_interior",
            type=DataType.BOOL,
            description="Keep object interiors unchanged (only colorize boundaries)",
            required=False,
            default=True,
        ),
        InputSchema(
            name="custom_instructions",
            type=DataType.STRING,
            description="Additional custom instructions for specific needs",
            required=False,
            default="",
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Output path (auto-generated if not provided)",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="colorized_image",
            type=DataType.IMAGE,
            description="Path to the image with colorized boundaries",
        ),
        OutputSchema(
            name="success",
            type=DataType.BOOL,
            description="Whether colorization succeeded",
        ),
        OutputSchema(
            name="error",
            type=DataType.STRING,
            description="Error message if failed",
        ),
        OutputSchema(
            name="token_usage",
            type=DataType.DICT,
            description="Token usage statistics",
        ),
    ],
    tags=["vlm", "colorize", "boundaries", "segmentation", "visualization", "gemini"],
    version="1.0.0",
)


def register_tools(registry) -> None:
    """Register boundary colorizer tool with the registry."""
    registry.register(COLORIZE_BOUNDARIES_SCHEMA, colorize_boundaries)
