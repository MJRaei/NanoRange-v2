"""
Built-in tools for NanoRange.

These tools provide basic image analysis functionality and serve
as examples for creating custom tools.

Categories:
- io: Image loading and saving
- preprocessing: Image enhancement and filtering
- segmentation: Object detection and masking
- measurement: Quantitative analysis
- vlm: Vision Language Model powered image processing
- ml: Machine learning based tools (Cellpose, etc.)
"""

from nanorange.tools.builtin.io_tools import register_tools as register_io
from nanorange.tools.builtin.preprocessing import register_tools as register_preprocessing
from nanorange.tools.builtin.segmentation import register_tools as register_segmentation
from nanorange.tools.builtin.measurement import register_tools as register_measurement
from nanorange.tools.builtin.vlm_tools import register_tools as register_vlm
from nanorange.tools.builtin.ml_tools import register_tools as register_ml


def register_all_tools(registry):
    """Register all built-in tools."""
    register_io(registry)
    register_preprocessing(registry)
    register_segmentation(registry)
    register_measurement(registry)
    register_vlm(registry)
    register_ml(registry)


def register_tools(registry):
    """Alias for register_all_tools."""
    register_all_tools(registry)
