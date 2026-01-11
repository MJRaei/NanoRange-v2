"""
Built-in tools for NanoRange.

These tools provide basic image analysis functionality and serve
as examples for creating custom tools.
"""

from nanorange.tools.builtin.io_tools import register_tools as register_io
from nanorange.tools.builtin.preprocessing import register_tools as register_preprocessing
from nanorange.tools.builtin.segmentation import register_tools as register_segmentation
from nanorange.tools.builtin.measurement import register_tools as register_measurement


def register_all_tools(registry):
    """Register all built-in tools."""
    register_io(registry)
    register_preprocessing(registry)
    register_segmentation(registry)
    register_measurement(registry)


def register_tools(registry):
    """Alias for register_all_tools."""
    register_all_tools(registry)
