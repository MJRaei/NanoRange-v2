"""
Cellpose segmentation tool for cell and nuclei detection.

This tool wraps the Cellpose deep learning model for instance segmentation.
It produces overlay visualizations and measurement CSVs that can be reviewed
by the agent for iterative refinement.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image
from scipy import ndimage

from nanorange.core.schemas import (
    DataType,
    InputSchema,
    OutputSchema,
    ToolSchema,
    ToolType,
)


def create_overlay(
    image: np.ndarray,
    masks: np.ndarray,
    alpha: float = 0.5,
    seed: int = 42
) -> np.ndarray:
    """
    Create colored overlay of masks on image.
    
    Args:
        image: Original image (grayscale or RGB)
        masks: Instance segmentation mask with unique labels
        alpha: Overlay transparency (0-1)
        seed: Random seed for consistent colors
        
    Returns:
        RGB overlay image as numpy array
    """
    if image.ndim == 2:
        overlay = np.stack([image] * 3, axis=-1)
    else:
        overlay = image.copy()
    overlay = overlay.astype(np.float32)
    
    unique_labels = np.unique(masks)
    unique_labels = unique_labels[unique_labels != 0]
    
    if len(unique_labels) == 0:
        return overlay.astype(np.uint8)
    
    np.random.seed(seed)
    colors = np.random.randint(50, 255, size=(len(unique_labels) + 1, 3), dtype=np.uint8)
    
    for idx, label in enumerate(unique_labels, 1):
        mask = masks == label
        color = colors[idx].astype(np.float32)
        for c in range(3):
            overlay[:, :, c] = np.where(
                mask,
                overlay[:, :, c] * (1 - alpha) + color[c] * alpha,
                overlay[:, :, c]
            )
    
    overlay = overlay.astype(np.uint8)
    
    for label in unique_labels:
        mask = masks == label
        eroded = ndimage.binary_erosion(mask, iterations=1)
        boundary = mask & ~eroded
        overlay[boundary] = [255, 255, 255]
    
    return overlay


def create_colored_mask(masks: np.ndarray, seed: int = 123) -> np.ndarray:
    """
    Convert mask labels to RGB colored image.
    
    Args:
        masks: Instance segmentation mask
        seed: Random seed for colors
        
    Returns:
        RGB colored mask image
    """
    if masks.max() == 0:
        return np.zeros((*masks.shape, 3), dtype=np.uint8)
    
    np.random.seed(seed)
    colors = np.random.randint(30, 255, size=(masks.max() + 1, 3), dtype=np.uint8)
    colors[0] = [0, 0, 0]
    
    colored = np.zeros((*masks.shape, 3), dtype=np.uint8)
    unique_labels = np.unique(masks)
    unique_labels = unique_labels[unique_labels != 0]
    
    for label in unique_labels:
        colored[masks == label] = colors[label]
    
    return colored


def compute_measurements(masks: np.ndarray) -> List[Dict[str, Any]]:
    """
    Compute measurements for each segmented object.
    
    Args:
        masks: Instance segmentation mask
        
    Returns:
        List of dictionaries containing measurements for each object
    """
    unique_labels = np.unique(masks)
    unique_labels = unique_labels[unique_labels != 0]
    
    measurements = []
    for label in unique_labels:
        mask = masks == label
        area = int(np.sum(mask))
        
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not np.any(rows) or not np.any(cols):
            continue
            
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        
        centroid_y, centroid_x = ndimage.center_of_mass(mask)
        
        eroded = ndimage.binary_erosion(mask, iterations=1)
        boundary = mask & ~eroded
        perimeter = int(np.sum(boundary))
        
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter ** 2)
        else:
            circularity = 0.0
        
        equivalent_diameter = np.sqrt(4 * area / np.pi)
        
        measurements.append({
            'Object_ID': int(label),
            'Area_px': area,
            'Perimeter_px': perimeter,
            'Circularity': round(circularity, 4),
            'Equivalent_Diameter_px': round(equivalent_diameter, 2),
            'Centroid_X': round(centroid_x, 2),
            'Centroid_Y': round(centroid_y, 2),
            'BBox_X_min': int(cmin),
            'BBox_Y_min': int(rmin),
            'BBox_X_max': int(cmax),
            'BBox_Y_max': int(rmax),
            'Width_px': int(cmax - cmin + 1),
            'Height_px': int(rmax - rmin + 1),
        })
    
    measurements.sort(key=lambda x: x['Object_ID'])
    return measurements


def save_measurements_csv(measurements: List[Dict], output_path: str) -> None:
    """Save measurements to CSV file."""
    if not measurements:
        fieldnames = [
            'Object_ID', 'Area_px', 'Perimeter_px', 'Circularity',
            'Equivalent_Diameter_px', 'Centroid_X', 'Centroid_Y',
            'BBox_X_min', 'BBox_Y_min', 'BBox_X_max', 'BBox_Y_max',
            'Width_px', 'Height_px'
        ]
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    fieldnames = list(measurements[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(measurements)


def cellpose_segment(
    image_path: str,
    model_type: str = "nuclei",
    diameter: float = 30.0,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    use_gpu: bool = True,
    min_size: int = 15,
    output_dir: Optional[str] = None,
    overlay_alpha: float = 0.5,
) -> Dict[str, Any]:
    """
    Segment cells or nuclei using Cellpose deep learning model.
    
    This tool runs Cellpose instance segmentation on an image and produces:
    - An overlay visualization showing detected objects
    - A colored mask image
    - A raw instance mask (16-bit PNG)
    - A CSV file with measurements for each detected object
    
    The agent can review the overlay image and re-run with different parameters
    to refine the segmentation results.
    
    Args:
        image_path: Path to the input image to segment.
        model_type: Cellpose model type. Options:
            - "nuclei": For round nuclei detection (DAPI, Hoechst stained)
            - "cyto": For cell body segmentation (cytoplasm)
            - "cyto2": Improved cytoplasm model
            - "cyto3": Latest cytoplasm model
            - "cpsam": Cellpose-SAM for general segmentation
            - "tissuenet_cp3": General tissue segmentation
            - "livecell_cp3": Live cell imaging
            - Custom model path can also be provided
        diameter: Expected diameter of objects in pixels. Use smaller values
            for detecting smaller objects. Set to 0 for auto-estimation.
            Typical values: 15-30 for nuclei, 30-100 for cells.
        flow_threshold: Flow error threshold (0.0-1.0). Lower values are more
            stringent and may split objects. Default 0.4 works well.
        cellprob_threshold: Cell probability threshold (-6.0 to 6.0). Lower
            values detect more objects (more sensitive). Default 0.0.
            Use negative values (-1 to -3) for faint objects.
        use_gpu: Whether to use GPU acceleration if available.
        min_size: Minimum object size in pixels. Objects smaller than this
            are removed. Default 15.
        output_dir: Directory to save outputs. Defaults to a subfolder
            in the same directory as the input image.
        overlay_alpha: Transparency of the overlay (0-1). Default 0.5.
    
    Returns:
        Dictionary with:
        - object_count: Number of detected objects
        - overlay_image: Path to overlay visualization (for agent review)
        - mask_image: Path to colored mask image
        - raw_mask: Path to raw instance mask (16-bit)
        - measurements_csv: Path to CSV with object measurements
        - summary: Text summary of detection results
        - parameters_used: Dict of parameters used for this run
    """
    from cellpose import models
    
    try:
        from importlib.metadata import version as get_version
        cellpose_version = get_version('cellpose')
        major_version = int(cellpose_version.split('.')[0])
        is_v4_plus = major_version >= 4
    except Exception:
        is_v4_plus = False
    
    source_path = Path(image_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if output_dir is None:
        output_dir = source_path.parent / f"cellpose_{model_type}_results"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image = np.array(Image.open(source_path))
    
    try:
        if is_v4_plus:
            model = models.CellposeModel(gpu=use_gpu, pretrained_model=model_type)
        else:
            model = models.CellposeModel(gpu=use_gpu, model_type=model_type)
    except Exception as e:
        if use_gpu:
            try:
                if is_v4_plus:
                    model = models.CellposeModel(gpu=False, pretrained_model=model_type)
                else:
                    model = models.CellposeModel(gpu=False, model_type=model_type)
            except Exception:
                raise e
        else:
            raise e
    
    eval_kwargs = {
        'diameter': diameter if diameter > 0 else None,
        'flow_threshold': flow_threshold,
        'cellprob_threshold': cellprob_threshold,
        'min_size': min_size,
    }
    
    if not is_v4_plus:
        if image.ndim == 2:
            eval_kwargs['channels'] = [0, 0]
        else:
            eval_kwargs['channels'] = [0, 0]
    
    masks, flows, styles = model.eval(image, **eval_kwargs)
    
    object_count = int(masks.max())
    
    base_name = source_path.stem
    
    overlay = create_overlay(image, masks, alpha=overlay_alpha)
    overlay_path = output_dir / f"{base_name}_overlay.png"
    Image.fromarray(overlay).save(overlay_path)
    
    colored_mask = create_colored_mask(masks)
    colored_mask_path = output_dir / f"{base_name}_mask_colored.png"
    Image.fromarray(colored_mask).save(colored_mask_path)
    
    raw_mask_path = output_dir / f"{base_name}_mask_raw.png"
    Image.fromarray(masks.astype(np.uint16)).save(raw_mask_path)
    
    measurements = compute_measurements(masks)
    csv_path = output_dir / f"{base_name}_measurements.csv"
    save_measurements_csv(measurements, str(csv_path))
    
    if measurements:
        areas = [m['Area_px'] for m in measurements]
        circularities = [m['Circularity'] for m in measurements]
        summary = (
            f"Detected {object_count} objects using Cellpose ({model_type} model).\n"
            f"Area range: {min(areas)} - {max(areas)} px (mean: {np.mean(areas):.1f})\n"
            f"Mean circularity: {np.mean(circularities):.3f}\n"
            f"Parameters: diameter={diameter}, flow_threshold={flow_threshold}, "
            f"cellprob_threshold={cellprob_threshold}"
        )
    else:
        summary = (
            f"No objects detected with current parameters.\n"
            f"Try adjusting: lower cellprob_threshold (e.g., -2), "
            f"different diameter, or different model_type."
        )
    
    parameters_used = {
        "model_type": model_type,
        "diameter": diameter,
        "flow_threshold": flow_threshold,
        "cellprob_threshold": cellprob_threshold,
        "use_gpu": use_gpu,
        "min_size": min_size,
        "overlay_alpha": overlay_alpha,
    }
    
    return {
        "object_count": object_count,
        "overlay_image": str(overlay_path),
        "mask_image": str(colored_mask_path),
        "raw_mask": str(raw_mask_path),
        "measurements_csv": str(csv_path),
        "summary": summary,
        "parameters_used": parameters_used,
    }


CELLPOSE_SEGMENT_SCHEMA = ToolSchema(
    tool_id="cellpose_segment",
    name="Cellpose Segmentation",
    description=(
        "Segment cells or nuclei using Cellpose deep learning model. "
        "Produces overlay visualization, mask images, and CSV measurements. "
        "The overlay can be reviewed and the tool re-run with different "
        "parameters for iterative refinement. Supports multiple model types "
        "for different imaging scenarios."
    ),
    type=ToolType.FUNCTION,
    category="ml_segmentation",
    inputs=[
        InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to the input image to segment",
            required=True,
        ),
        InputSchema(
            name="model_type",
            type=DataType.STRING,
            description=(
                "Cellpose model type: 'nuclei' for round nuclei (DAPI/Hoechst), "
                "'cyto'/'cyto2'/'cyto3' for cell bodies, 'cpsam' for general "
                "segmentation (Cellpose-SAM), 'tissuenet_cp3' for tissue, "
                "'livecell_cp3' for live cells. Can also be a path to custom model."
            ),
            required=False,
            default="nuclei",
            choices=["nuclei", "cyto", "cyto2", "cyto3", "cpsam", "tissuenet_cp3", "livecell_cp3"],
        ),
        InputSchema(
            name="diameter",
            type=DataType.FLOAT,
            description=(
                "Expected object diameter in pixels. Smaller values detect "
                "smaller objects. Set to 0 for auto-estimation. Typical values: "
                "15-30 for nuclei, 30-100 for cells."
            ),
            required=False,
            default=30.0,
            min_value=0.0,
            max_value=500.0,
        ),
        InputSchema(
            name="flow_threshold",
            type=DataType.FLOAT,
            description=(
                "Flow error threshold (0.0-1.0). Lower values are more "
                "stringent and may split merged objects. Default 0.4 works well."
            ),
            required=False,
            default=0.4,
            min_value=0.0,
            max_value=1.0,
        ),
        InputSchema(
            name="cellprob_threshold",
            type=DataType.FLOAT,
            description=(
                "Cell probability threshold (-6.0 to 6.0). Lower values "
                "detect more objects (more sensitive). Use negative values "
                "(-1 to -3) for faint or low-contrast objects. Default 0.0."
            ),
            required=False,
            default=0.0,
            min_value=-6.0,
            max_value=6.0,
        ),
        InputSchema(
            name="use_gpu",
            type=DataType.BOOL,
            description="Whether to use GPU acceleration if available",
            required=False,
            default=True,
        ),
        InputSchema(
            name="min_size",
            type=DataType.INT,
            description="Minimum object size in pixels (smaller objects removed)",
            required=False,
            default=15,
            min_value=1,
            max_value=1000,
        ),
        InputSchema(
            name="output_dir",
            type=DataType.PATH,
            description="Output directory path. Defaults to subfolder of input image.",
            required=False,
        ),
        InputSchema(
            name="overlay_alpha",
            type=DataType.FLOAT,
            description="Overlay transparency (0-1). Higher = more opaque overlay.",
            required=False,
            default=0.5,
            min_value=0.0,
            max_value=1.0,
        ),
    ],
    outputs=[
        OutputSchema(
            name="object_count",
            type=DataType.INT,
            description="Number of detected objects",
        ),
        OutputSchema(
            name="overlay_image",
            type=DataType.IMAGE,
            description="Path to overlay visualization for review",
        ),
        OutputSchema(
            name="mask_image",
            type=DataType.IMAGE,
            description="Path to colored mask image",
        ),
        OutputSchema(
            name="raw_mask",
            type=DataType.MASK,
            description="Path to raw instance mask (16-bit)",
        ),
        OutputSchema(
            name="measurements_csv",
            type=DataType.PATH,
            description="Path to CSV file with object measurements",
        ),
        OutputSchema(
            name="summary",
            type=DataType.STRING,
            description="Text summary of detection results",
        ),
        OutputSchema(
            name="parameters_used",
            type=DataType.DICT,
            description="Dictionary of parameters used for this run",
        ),
    ],
    tags=[
        "cellpose", "segmentation", "cells", "nuclei", "deep-learning",
        "instance-segmentation", "ml", "refinable", "iterative"
    ],
    version="1.0.0",
)
