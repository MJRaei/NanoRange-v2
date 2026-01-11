"""
Segmentation tools for object detection and masking.
"""

from pathlib import Path
from typing import Any, Dict
from nanorange.core.schemas import DataType, InputSchema, OutputSchema, ToolSchema, ToolType


def threshold(
    image_path: str,
    threshold_value: float = 128,
    method: str = "binary",
    output_path: str = None
) -> Dict[str, Any]:
    """
    Apply threshold to create binary mask.
    
    Args:
        image_path: Path to input image
        threshold_value: Threshold value (0-255)
        method: Thresholding method (binary, binary_inv, otsu)
        output_path: Optional output path
        
    Returns:
        Dictionary with mask path and threshold used
    """
    from PIL import Image
    import numpy as np
    
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if output_path is None:
        output_path = str(source.parent / f"{source.stem}_mask{source.suffix}")
    
    # Load image as grayscale
    img = Image.open(source).convert('L')
    arr = np.array(img)
    
    # Determine threshold
    if method == "otsu":
        # Simple Otsu implementation
        hist, _ = np.histogram(arr.flatten(), bins=256, range=(0, 256))
        total = arr.size
        
        sum_total = np.sum(np.arange(256) * hist)
        sum_bg = 0
        weight_bg = 0
        max_variance = 0
        threshold_value = 0
        
        for t in range(256):
            weight_bg += hist[t]
            if weight_bg == 0:
                continue
            
            weight_fg = total - weight_bg
            if weight_fg == 0:
                break
            
            sum_bg += t * hist[t]
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_total - sum_bg) / weight_fg
            
            variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
            if variance > max_variance:
                max_variance = variance
                threshold_value = t
    
    # Apply threshold
    if method == "binary_inv":
        mask = (arr < threshold_value).astype(np.uint8) * 255
    else:
        mask = (arr >= threshold_value).astype(np.uint8) * 255
    
    # Save
    result = Image.fromarray(mask)
    result.save(output_path)
    
    return {
        "mask": output_path,
        "threshold_used": float(threshold_value)
    }


THRESHOLD_SCHEMA = ToolSchema(
    tool_id="threshold",
    name="Threshold",
    description="Apply intensity threshold to create binary mask",
    type=ToolType.FUNCTION,
    category="segmentation",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to input image",
            required=True,
        ),
        InputSchema(
            name="threshold_value",
            type=DataType.FLOAT,
            description="Threshold value (0-255), ignored if method=otsu",
            required=False,
            default=128,
            min_value=0,
            max_value=255,
        ),
        InputSchema(
            name="method",
            type=DataType.STRING,
            description="Thresholding method",
            required=False,
            default="binary",
            choices=["binary", "binary_inv", "otsu"],
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
            name="mask",
            type=DataType.MASK,
            description="Binary mask image",
        ),
        OutputSchema(
            name="threshold_used",
            type=DataType.FLOAT,
            description="Actual threshold value used",
        ),
    ],
    tags=["threshold", "binary", "mask", "segmentation"],
)


def find_contours(
    mask_path: str,
    min_area: int = 10,
    max_area: int = None
) -> Dict[str, Any]:
    """
    Find contours/objects in a binary mask.
    
    Args:
        mask_path: Path to binary mask image
        min_area: Minimum object area in pixels
        max_area: Maximum object area (None for no limit)
        
    Returns:
        Dictionary with object count and bounding boxes
    """
    from PIL import Image
    import numpy as np
    
    source = Path(mask_path)
    if not source.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")
    
    # Load mask
    img = Image.open(source).convert('L')
    mask = np.array(img) > 127
    
    # Simple connected component analysis
    from scipy import ndimage
    labeled, num_features = ndimage.label(mask)
    
    # Get object properties
    objects = []
    for i in range(1, num_features + 1):
        obj_mask = labeled == i
        area = np.sum(obj_mask)
        
        # Filter by area
        if area < min_area:
            continue
        if max_area is not None and area > max_area:
            continue
        
        # Get bounding box
        rows = np.any(obj_mask, axis=1)
        cols = np.any(obj_mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        
        objects.append({
            "id": len(objects) + 1,
            "area": int(area),
            "bbox": [int(cmin), int(rmin), int(cmax), int(rmax)],
            "centroid": [int((cmin + cmax) / 2), int((rmin + rmax) / 2)],
        })
    
    return {
        "object_count": len(objects),
        "objects": objects,
    }


FIND_CONTOURS_SCHEMA = ToolSchema(
    tool_id="find_contours",
    name="Find Contours",
    description="Find and count objects in a binary mask",
    type=ToolType.FUNCTION,
    category="segmentation",
    inputs=[
        InputSchema(
            name="mask_path",
            type=DataType.MASK,
            description="Path to binary mask",
            required=True,
        ),
        InputSchema(
            name="min_area",
            type=DataType.INT,
            description="Minimum object area in pixels",
            required=False,
            default=10,
            min_value=1,
        ),
        InputSchema(
            name="max_area",
            type=DataType.INT,
            description="Maximum object area (None for no limit)",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="object_count",
            type=DataType.INT,
            description="Number of objects found",
        ),
        OutputSchema(
            name="objects",
            type=DataType.LIST,
            description="List of object properties",
        ),
    ],
    tags=["contours", "objects", "detect", "count"],
)


def label_objects(
    mask_path: str,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Label connected components in a binary mask.
    
    Args:
        mask_path: Path to binary mask
        output_path: Output path for labeled image
        
    Returns:
        Dictionary with labeled image path and object count
    """
    from PIL import Image
    import numpy as np
    from scipy import ndimage
    
    source = Path(mask_path)
    if not source.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")
    
    if output_path is None:
        output_path = str(source.parent / f"{source.stem}_labeled{source.suffix}")
    
    # Load mask
    img = Image.open(source).convert('L')
    mask = np.array(img) > 127
    
    # Label connected components
    labeled, num_features = ndimage.label(mask)
    
    # Normalize for visualization (each label gets different intensity)
    if num_features > 0:
        labeled_vis = ((labeled / num_features) * 255).astype(np.uint8)
    else:
        labeled_vis = np.zeros_like(mask, dtype=np.uint8)
    
    # Save
    result = Image.fromarray(labeled_vis)
    result.save(output_path)
    
    return {
        "labeled_image": output_path,
        "num_objects": int(num_features),
    }


LABEL_OBJECTS_SCHEMA = ToolSchema(
    tool_id="label_objects",
    name="Label Objects",
    description="Label connected components in a binary mask",
    type=ToolType.FUNCTION,
    category="segmentation",
    inputs=[
        InputSchema(
            name="mask_path",
            type=DataType.MASK,
            description="Path to binary mask",
            required=True,
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Output path for labeled image",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="labeled_image",
            type=DataType.IMAGE,
            description="Labeled image (each object has unique intensity)",
        ),
        OutputSchema(
            name="num_objects",
            type=DataType.INT,
            description="Number of labeled objects",
        ),
    ],
    tags=["label", "connected", "components"],
)


def register_tools(registry):
    """Register segmentation tools with the registry."""
    registry.register(THRESHOLD_SCHEMA, threshold)
    registry.register(FIND_CONTOURS_SCHEMA, find_contours)
    registry.register(LABEL_OBJECTS_SCHEMA, label_objects)
