"""
Measurement tools for extracting quantitative data from images.
"""

from pathlib import Path
from typing import Any, Dict, List
from nanorange.core.schemas import DataType, InputSchema, OutputSchema, ToolSchema, ToolType


def measure_intensity(
    image_path: str,
    mask_path: str = None
) -> Dict[str, Any]:
    """
    Measure intensity statistics of an image.
    
    Args:
        image_path: Path to input image
        mask_path: Optional mask to restrict measurement region
        
    Returns:
        Dictionary with intensity statistics
    """
    from PIL import Image
    import numpy as np
    
    source = Path(image_path)
    if not source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image
    img = Image.open(source).convert('L')
    arr = np.array(img, dtype=np.float32)
    
    # Apply mask if provided
    if mask_path:
        mask_source = Path(mask_path)
        if mask_source.exists():
            mask_img = Image.open(mask_source).convert('L')
            mask = np.array(mask_img) > 127
            arr = arr[mask]
    
    # Calculate statistics
    measurements = {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr)),
        "total": float(np.sum(arr)),
        "pixel_count": int(arr.size),
    }
    
    return {"measurements": measurements}


MEASURE_INTENSITY_SCHEMA = ToolSchema(
    tool_id="measure_intensity",
    name="Measure Intensity",
    description="Calculate intensity statistics for an image or masked region",
    type=ToolType.FUNCTION,
    category="measurement",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to input image",
            required=True,
        ),
        InputSchema(
            name="mask_path",
            type=DataType.MASK,
            description="Optional mask to restrict measurement region",
            required=False,
        ),
    ],
    outputs=[
        OutputSchema(
            name="measurements",
            type=DataType.MEASUREMENTS,
            description="Intensity statistics (mean, std, min, max, median, total)",
        ),
    ],
    tags=["intensity", "statistics", "measure", "quantify"],
)


def measure_objects(
    image_path: str,
    mask_path: str
) -> Dict[str, Any]:
    """
    Measure properties of labeled objects.
    
    Args:
        image_path: Path to intensity image
        mask_path: Path to binary or labeled mask
        
    Returns:
        Dictionary with per-object measurements
    """
    from PIL import Image
    import numpy as np
    from scipy import ndimage
    
    img_source = Path(image_path)
    mask_source = Path(mask_path)
    
    if not img_source.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not mask_source.exists():
        raise FileNotFoundError(f"Mask not found: {mask_path}")
    
    # Load images
    img = Image.open(img_source).convert('L')
    intensity = np.array(img, dtype=np.float32)
    
    mask_img = Image.open(mask_source).convert('L')
    mask = np.array(mask_img)
    
    # Label if binary
    if mask.max() <= 1 or (mask > 0).sum() == (mask == mask.max()).sum():
        labeled, num_features = ndimage.label(mask > 127)
    else:
        labeled = mask
        num_features = mask.max()
    
    # Measure each object
    object_measurements = []
    
    for i in range(1, num_features + 1):
        obj_mask = labeled == i
        obj_intensity = intensity[obj_mask]
        
        # Get object properties
        rows, cols = np.where(obj_mask)
        
        measurement = {
            "id": i,
            "area": int(np.sum(obj_mask)),
            "mean_intensity": float(np.mean(obj_intensity)),
            "std_intensity": float(np.std(obj_intensity)),
            "min_intensity": float(np.min(obj_intensity)),
            "max_intensity": float(np.max(obj_intensity)),
            "total_intensity": float(np.sum(obj_intensity)),
            "centroid_y": float(np.mean(rows)),
            "centroid_x": float(np.mean(cols)),
            "bbox": [int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())],
        }
        
        object_measurements.append(measurement)
    
    # Summary statistics
    summary = {
        "object_count": len(object_measurements),
        "total_area": sum(m["area"] for m in object_measurements),
        "mean_area": float(np.mean([m["area"] for m in object_measurements])) if object_measurements else 0,
        "mean_intensity_all": float(np.mean([m["mean_intensity"] for m in object_measurements])) if object_measurements else 0,
    }
    
    return {
        "object_measurements": object_measurements,
        "summary": summary,
    }


MEASURE_OBJECTS_SCHEMA = ToolSchema(
    tool_id="measure_objects",
    name="Measure Objects",
    description="Measure properties of objects defined by a mask",
    type=ToolType.FUNCTION,
    category="measurement",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to intensity image",
            required=True,
        ),
        InputSchema(
            name="mask_path",
            type=DataType.MASK,
            description="Path to object mask",
            required=True,
        ),
    ],
    outputs=[
        OutputSchema(
            name="object_measurements",
            type=DataType.LIST,
            description="Per-object measurements",
        ),
        OutputSchema(
            name="summary",
            type=DataType.MEASUREMENTS,
            description="Summary statistics across all objects",
        ),
    ],
    tags=["objects", "measure", "area", "intensity", "properties"],
)


def export_measurements(
    measurements: Dict[str, Any],
    output_path: str,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Export measurements to a file.
    
    Args:
        measurements: Measurements to export
        output_path: Output file path
        format: Output format (json, csv)
        
    Returns:
        Dictionary with export path
    """
    import json
    
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "csv":
        # Convert to CSV
        if isinstance(measurements, list):
            # List of dicts -> CSV
            if measurements:
                keys = measurements[0].keys()
                lines = [",".join(str(k) for k in keys)]
                for m in measurements:
                    lines.append(",".join(str(m.get(k, "")) for k in keys))
                dest.write_text("\n".join(lines))
        else:
            # Single dict -> CSV
            lines = ["key,value"]
            for k, v in measurements.items():
                lines.append(f"{k},{v}")
            dest.write_text("\n".join(lines))
    else:
        # JSON format
        with open(dest, 'w') as f:
            json.dump(measurements, f, indent=2, default=str)
    
    return {"export_path": str(dest.absolute())}


EXPORT_MEASUREMENTS_SCHEMA = ToolSchema(
    tool_id="export_measurements",
    name="Export Measurements",
    description="Export measurements to JSON or CSV file",
    type=ToolType.FUNCTION,
    category="measurement",
    inputs=[
        InputSchema(
            name="measurements",
            type=DataType.MEASUREMENTS,
            description="Measurements to export",
            required=True,
        ),
        InputSchema(
            name="output_path",
            type=DataType.PATH,
            description="Output file path",
            required=True,
        ),
        InputSchema(
            name="format",
            type=DataType.STRING,
            description="Output format",
            required=False,
            default="json",
            choices=["json", "csv"],
        ),
    ],
    outputs=[
        OutputSchema(
            name="export_path",
            type=DataType.PATH,
            description="Path to exported file",
        ),
    ],
    tags=["export", "save", "csv", "json"],
)


def register_tools(registry):
    """Register measurement tools with the registry."""
    registry.register(MEASURE_INTENSITY_SCHEMA, measure_intensity)
    registry.register(MEASURE_OBJECTS_SCHEMA, measure_objects)
    registry.register(EXPORT_MEASUREMENTS_SCHEMA, export_measurements)
