"""
Preprocessing tools for image enhancement and noise reduction.
"""

from pathlib import Path
from typing import Any, Dict
from nanorange.core.schemas import DataType, InputSchema, OutputSchema, ToolSchema, ToolType


def gaussian_blur(
    image_path: str,
    sigma: float = 1.0,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Apply Gaussian blur to reduce noise.
    
    Args:
        image_path: Path to input image
        sigma: Standard deviation for Gaussian kernel
        output_path: Optional output path (auto-generated if not provided)
        
    Returns:
        Dictionary with blurred image path
    """
    from PIL import Image, ImageFilter
    
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Generate output path if not provided
    if output_path is None:
        output_path = str(source.parent / f"{source.stem}_blurred{source.suffix}")
    
    # Load and process image
    img = Image.open(source)
    
    # PIL's GaussianBlur uses radius, sigma ≈ radius/2
    radius = int(sigma * 2)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=max(1, radius)))
    
    # Save
    blurred.save(output_path)
    
    return {"blurred_image": output_path}


GAUSSIAN_BLUR_SCHEMA = ToolSchema(
    tool_id="gaussian_blur",
    name="Gaussian Blur",
    description="Apply Gaussian blur to smooth image and reduce noise",
    type=ToolType.FUNCTION,
    category="preprocessing",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to input image",
            required=True,
        ),
        InputSchema(
            name="sigma",
            type=DataType.FLOAT,
            description="Standard deviation for Gaussian kernel",
            required=False,
            default=1.0,
            min_value=0.1,
            max_value=10.0,
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
            name="blurred_image",
            type=DataType.IMAGE,
            description="Path to blurred image",
        ),
    ],
    tags=["blur", "smooth", "noise", "filter"],
)


def normalize_intensity(
    image_path: str,
    min_percentile: float = 1.0,
    max_percentile: float = 99.0,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Normalize image intensity to enhance contrast.
    
    Args:
        image_path: Path to input image
        min_percentile: Lower percentile for normalization
        max_percentile: Upper percentile for normalization
        output_path: Optional output path
        
    Returns:
        Dictionary with normalized image path
    """
    from PIL import Image
    import numpy as np
    
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if output_path is None:
        output_path = str(source.parent / f"{source.stem}_normalized{source.suffix}")
    
    # Load image
    img = Image.open(source)
    arr = np.array(img, dtype=np.float32)
    
    # Calculate percentiles
    p_low = np.percentile(arr, min_percentile)
    p_high = np.percentile(arr, max_percentile)
    
    # Normalize
    if p_high > p_low:
        arr = (arr - p_low) / (p_high - p_low)
        arr = np.clip(arr, 0, 1) * 255
    
    # Save
    result = Image.fromarray(arr.astype(np.uint8))
    result.save(output_path)
    
    return {
        "normalized_image": output_path,
        "intensity_range": {"min": float(p_low), "max": float(p_high)}
    }


NORMALIZE_INTENSITY_SCHEMA = ToolSchema(
    tool_id="normalize_intensity",
    name="Normalize Intensity",
    description="Normalize image intensity using percentile-based contrast stretching",
    type=ToolType.FUNCTION,
    category="preprocessing",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to input image",
            required=True,
        ),
        InputSchema(
            name="min_percentile",
            type=DataType.FLOAT,
            description="Lower percentile for normalization",
            required=False,
            default=1.0,
            min_value=0.0,
            max_value=50.0,
        ),
        InputSchema(
            name="max_percentile",
            type=DataType.FLOAT,
            description="Upper percentile for normalization",
            required=False,
            default=99.0,
            min_value=50.0,
            max_value=100.0,
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Output path",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="normalized_image",
            type=DataType.IMAGE,
            description="Path to normalized image",
        ),
        OutputSchema(
            name="intensity_range",
            type=DataType.DICT,
            description="Original intensity range used for normalization",
        ),
    ],
    tags=["normalize", "contrast", "intensity", "enhance"],
)


def invert_image(
    image_path: str,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Invert image colors/intensities.
    
    Args:
        image_path: Path to input image
        output_path: Optional output path
        
    Returns:
        Dictionary with inverted image path
    """
    from PIL import Image, ImageOps
    
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if output_path is None:
        output_path = str(source.parent / f"{source.stem}_inverted{source.suffix}")
    
    img = Image.open(source)
    inverted = ImageOps.invert(img.convert('RGB'))
    inverted.save(output_path)
    
    return {"inverted_image": output_path}


INVERT_IMAGE_SCHEMA = ToolSchema(
    tool_id="invert_image",
    name="Invert Image",
    description="Invert image colors (negative)",
    type=ToolType.FUNCTION,
    category="preprocessing",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to input image",
            required=True,
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Output path",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="inverted_image",
            type=DataType.IMAGE,
            description="Path to inverted image",
        ),
    ],
    tags=["invert", "negative"],
)


def register_tools(registry):
    """Register preprocessing tools with the registry."""
    registry.register(GAUSSIAN_BLUR_SCHEMA, gaussian_blur)
    registry.register(NORMALIZE_INTENSITY_SCHEMA, normalize_intensity)
    registry.register(INVERT_IMAGE_SCHEMA, invert_image)
