"""
AI-powered image enhancement tool.

Uses Gemini's image generation capabilities to:
- Enhance contrast
- Remove noise and artifacts
- Sharpen boundaries
- Clean up images for analysis
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
from nanorange.settings import IMAGE_MODEL
from nanorange.tools.builtin.vlm_tools.base_image_agent import BaseImageAgent


class ImageEnhancerAgent(BaseImageAgent):
    """
    AI agent for image enhancement and preprocessing.
    
    Configurable for different enhancement tasks through instructions.
    """
    
    def __init__(self, model: Optional[str] = None) -> None:
        """
        Initialize the Image Enhancer Agent.
        
        Args:
            model: Gemini model to use (defaults to IMAGE_MODEL from settings)
        """
        super().__init__(
            model=model or IMAGE_MODEL,
            instruction=None  # Will be provided at runtime
        )


def build_enhancement_instruction(
    background_color: str = "black",
    foreground_color: str = "white",
    remove_noise: bool = True,
    sharpen_edges: bool = True,
    preserve_shapes: bool = True,
    flat_lighting: bool = True,
    additional_instructions: str = ""
) -> str:
    """
    Build a customized enhancement instruction prompt.
    
    Args:
        background_color: Target background color (e.g., "black", "#000000", "white")
        foreground_color: Target foreground/object color (e.g., "white", "#FFFFFF", "black")
        remove_noise: Whether to remove noise and tiny artifacts
        sharpen_edges: Whether to sharpen object edges
        preserve_shapes: Whether to preserve original shape appearance
        flat_lighting: Whether to use flat lighting (no gradients/shadows)
        additional_instructions: Any additional custom instructions
        
    Returns:
        Complete instruction string for the model
    """
    instructions = []
    
    # Background instruction
    instructions.append(
        f"Make the background COMPLETELY pure {background_color}."
    )
    
    # Foreground/edges instruction
    if sharpen_edges:
        instructions.append(
            f"Sharpen all object edges and boundaries, making them pure {foreground_color} "
            "with consistent thickness throughout the image."
        )
    
    # Noise removal
    if remove_noise:
        instructions.append(
            "Remove all noise, tiny artifacts, and unwanted specks from the image."
        )
    
    # Shape preservation
    if preserve_shapes:
        instructions.append(
            "Preserve the exact shape, size, and position of all objects in the image. "
            "Do not distort, add, or remove any significant features."
        )
    
    # Lighting
    if flat_lighting:
        instructions.append(
            "Use FLAT LIGHTING ONLY: Do not add any simulated light sources, shadows, "
            "or gradients. The lighting must be perfectly even across the entire image."
        )
    
    # Additional instructions
    if additional_instructions:
        instructions.append(additional_instructions)
    
    # Output instruction
    instructions.append(
        "Return ONLY the processed image with high contrast and clean boundaries."
    )
    
    return " ".join(instructions)


def ai_enhance_image(
    image_path: str,
    background_color: str = "black",
    foreground_color: str = "white",
    remove_noise: bool = True,
    sharpen_edges: bool = True,
    preserve_shapes: bool = True,
    flat_lighting: bool = True,
    custom_instructions: str = "",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhance an image using AI-powered processing.
    
    Uses Gemini's image generation to clean up microscopy images by:
    - Adjusting background and foreground contrast
    - Removing noise and artifacts
    - Sharpening object boundaries
    - Preserving original shapes
    
    Args:
        image_path: Path to the input image
        background_color: Target background color (e.g., "black", "white", "#000000")
        foreground_color: Target foreground/object color
        remove_noise: Remove noise and tiny artifacts
        sharpen_edges: Sharpen object edges and boundaries
        preserve_shapes: Preserve original shape appearance
        flat_lighting: Use flat lighting (no gradients/shadows)
        custom_instructions: Additional custom instructions for the model
        output_path: Output path (auto-generated if not provided)
        
    Returns:
        Dictionary with:
        - enhanced_image: Path to enhanced image (or None if failed)
        - success: Whether processing succeeded
        - error: Error message if failed
        - token_usage: Token usage statistics
    """
    source = Path(image_path)
    
    if not source.exists():
        return {
            "enhanced_image": None,
            "success": False,
            "error": f"Image not found: {image_path}",
            "token_usage": {},
        }
    
    # Generate output path if not provided
    if output_path is None:
        output_path = str(
            source.parent / f"{source.stem}_enhanced{source.suffix}"
        )
    
    # Build instruction
    instruction = build_enhancement_instruction(
        background_color=background_color,
        foreground_color=foreground_color,
        remove_noise=remove_noise,
        sharpen_edges=sharpen_edges,
        preserve_shapes=preserve_shapes,
        flat_lighting=flat_lighting,
        additional_instructions=custom_instructions,
    )
    
    # Create agent and process
    agent = ImageEnhancerAgent()
    result = agent.process_image(
        input_path=image_path,
        output_path=output_path,
        instruction=instruction,
    )
    
    return {
        "enhanced_image": result.get("output_path"),
        "success": result.get("success", False),
        "error": result.get("error"),
        "token_usage": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
        },
    }


# Tool Schema Definition
AI_ENHANCE_IMAGE_SCHEMA = ToolSchema(
    tool_id="ai_enhance_image",
    name="AI Image Enhancer",
    description=(
        "Enhance microscopy images using AI. Cleans up images by adjusting contrast, "
        "removing noise, sharpening boundaries, and separating objects from background. "
        "Highly configurable for different image types and analysis needs."
    ),
    type=ToolType.AGENT,
    category="vlm",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to the input image to enhance",
            required=True,
        ),
        InputSchema(
            name="background_color",
            type=DataType.STRING,
            description="Target background color (e.g., 'black', 'white', '#000000')",
            required=False,
            default="black",
        ),
        InputSchema(
            name="foreground_color",
            type=DataType.STRING,
            description="Target foreground/object color (e.g., 'white', 'black', '#FFFFFF')",
            required=False,
            default="white",
        ),
        InputSchema(
            name="remove_noise",
            type=DataType.BOOL,
            description="Remove noise and tiny artifacts",
            required=False,
            default=True,
        ),
        InputSchema(
            name="sharpen_edges",
            type=DataType.BOOL,
            description="Sharpen object edges and boundaries",
            required=False,
            default=True,
        ),
        InputSchema(
            name="preserve_shapes",
            type=DataType.BOOL,
            description="Preserve original shape appearance",
            required=False,
            default=True,
        ),
        InputSchema(
            name="flat_lighting",
            type=DataType.BOOL,
            description="Use flat lighting (no gradients/shadows)",
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
            name="enhanced_image",
            type=DataType.IMAGE,
            description="Path to the enhanced image",
        ),
        OutputSchema(
            name="success",
            type=DataType.BOOL,
            description="Whether enhancement succeeded",
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
    tags=["vlm", "enhance", "contrast", "denoise", "cleanup", "gemini"],
    version="1.0.0",
)


def register_tools(registry) -> None:
    """Register AI tools with the registry."""
    registry.register(AI_ENHANCE_IMAGE_SCHEMA, ai_enhance_image)
