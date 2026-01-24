"""
I/O tools for loading and saving images.
"""

from pathlib import Path
from typing import Any, Dict
from nanorange.core.schemas import DataType, InputSchema, OutputSchema, ToolSchema, ToolType


def load_image(image_path: str) -> Dict[str, Any]:
    """
    Load an image from disk.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with loaded image path and metadata
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Get basic info without loading full image
    # In a real implementation, you might use PIL or numpy to get dimensions
    return {
        "image": str(path.absolute()),
        "metadata": {
            "filename": path.name,
            "extension": path.suffix,
            "size_bytes": path.stat().st_size,
        }
    }


LOAD_IMAGE_SCHEMA = ToolSchema(
    tool_id="load_image",
    name="Load Image",
    description="Load an image from disk for analysis",
    type=ToolType.FUNCTION,
    category="io",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.PATH,
            description="Path to the image file",
            required=True,
        ),
    ],
    outputs=[
        OutputSchema(
            name="image",
            type=DataType.IMAGE,
            description="Loaded image path",
        ),
        OutputSchema(
            name="metadata",
            type=DataType.DICT,
            description="Image metadata",
        ),
    ],
    tags=["load", "input", "file"],
)


def save_image(
    image_path: str,
    output_path: str,
    format: str = "png"
) -> Dict[str, Any]:
    """
    Save an image to disk.

    Args:
        image_path: Path to source image
        output_path: Path to save the image (can be file path or directory)
        format: Output format (png, jpg, tiff)

    Returns:
        Dictionary with saved image path
    """
    import shutil

    source = Path(image_path)
    dest = Path(output_path)

    if not source.exists():
        raise FileNotFoundError(f"Source image not found: {image_path}")

    if dest.is_dir():
        actual_dest = dest / source.name
    else:
        actual_dest = dest

    actual_dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, actual_dest)

    return {"saved_path": str(actual_dest.absolute())}


SAVE_IMAGE_SCHEMA = ToolSchema(
    tool_id="save_image",
    name="Save Image",
    description="Save an image to disk",
    type=ToolType.FUNCTION,
    category="io",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to the image to save",
            required=True,
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Destination path",
            required=True,
        ),
        InputSchema(
            name="format",
            type=DataType.STRING,
            description="Output format",
            required=False,
            default="png",
            choices=["png", "jpg", "tiff"],
        ),
    ],
    outputs=[
        OutputSchema(
            name="saved_path",
            type=DataType.PATH,
            description="Path to saved image",
        ),
    ],
    tags=["save", "output", "file"],
)


def register_tools(registry):
    """Register I/O tools with the registry."""
    registry.register(LOAD_IMAGE_SCHEMA, load_image)
    registry.register(SAVE_IMAGE_SCHEMA, save_image)
