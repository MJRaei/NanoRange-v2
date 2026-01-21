"""
ML-based tools for NanoRange.

These tools wrap machine learning models for advanced image analysis tasks
like cell/nuclei segmentation, object detection, etc.

The outputs from these tools (images) can be reviewed by the agent and
the tools can be re-run with different parameters for refinement.

Categories:
- segmentation: ML-based segmentation (Cellpose, StarDist, etc.)
"""

from nanorange.tools.builtin.ml_tools.cellpose_segmentation import (
    cellpose_segment,
    CELLPOSE_SEGMENT_SCHEMA,
)


def register_tools(registry):
    """Register all ML tools with the registry."""
    registry.register(CELLPOSE_SEGMENT_SCHEMA, cellpose_segment)


__all__ = [
    "cellpose_segment",
    "CELLPOSE_SEGMENT_SCHEMA",
    "register_tools",
]
