"""
Image utility functions.

Provides helpers for:
- Getting image information
- Path manipulation
- Format detection
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def get_image_info(image_path: str) -> Dict[str, Any]:
    """
    Get basic information about an image file.
    
    Args:
        image_path: Path to the image
        
    Returns:
        Dictionary with image information
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    info = {
        "path": str(path.absolute()),
        "filename": path.name,
        "stem": path.stem,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
    }
    
    # Try to get image dimensions
    try:
        from PIL import Image
        with Image.open(path) as img:
            info["width"] = img.width
            info["height"] = img.height
            info["mode"] = img.mode
            info["format"] = img.format
    except Exception:
        pass
    
    return info


def ensure_image_path(path: str) -> Path:
    """
    Ensure a path exists and is an image file.
    
    Args:
        path: Path to check
        
    Returns:
        Path object
        
    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If path is not a supported image format
    """
    p = Path(path)
    
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    supported = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'}
    if p.suffix.lower() not in supported:
        raise ValueError(
            f"Unsupported image format: {p.suffix}. "
            f"Supported: {', '.join(supported)}"
        )
    
    return p


def generate_output_path(
    input_path: str,
    suffix: str = "_output",
    extension: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Generate an output path based on input path.
    
    Args:
        input_path: Input file path
        suffix: Suffix to add to filename
        extension: New extension (None to keep original)
        output_dir: Output directory (None to use input directory)
        
    Returns:
        Generated output path
    """
    path = Path(input_path)
    
    new_stem = f"{path.stem}{suffix}"
    new_ext = extension if extension else path.suffix
    
    if output_dir:
        output_path = Path(output_dir) / f"{new_stem}{new_ext}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = path.parent / f"{new_stem}{new_ext}"
    
    return str(output_path)


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """
    Get image dimensions without loading full image.
    
    Args:
        image_path: Path to image
        
    Returns:
        Tuple of (width, height)
    """
    from PIL import Image
    
    with Image.open(image_path) as img:
        return img.size


def is_grayscale(image_path: str) -> bool:
    """
    Check if an image is grayscale.
    
    Args:
        image_path: Path to image
        
    Returns:
        True if grayscale, False otherwise
    """
    from PIL import Image
    
    with Image.open(image_path) as img:
        return img.mode in ('L', 'LA', 'I', 'F')
