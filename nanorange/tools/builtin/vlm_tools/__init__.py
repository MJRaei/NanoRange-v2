"""
Vision Language Model (VLM) powered image processing tools.

These tools use Gemini's vision and image generation capabilities for
advanced image processing tasks.

Available tools:
- ai_enhance_image: Gemini-powered contrast enhancement, noise removal, boundary sharpening
- colorize_boundaries: Assign distinct colors to object boundaries
"""

from nanorange.tools.builtin.vlm_tools.image_enhancer import (
    register_tools as register_enhancer,
)
from nanorange.tools.builtin.vlm_tools.boundary_colorizer import (
    register_tools as register_colorizer,
)


def register_tools(registry) -> None:
    """Register all VLM tools with the registry."""
    register_enhancer(registry)
    register_colorizer(registry)


__all__ = ["register_tools"]
