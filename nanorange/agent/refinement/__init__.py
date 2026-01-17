"""
Iterative Refinement System for NanoRange.

This package provides adaptive pipeline execution that:
- Reviews tool outputs using an image reviewer model
- Adjusts parameters to improve results
- Removes tools that don't work for specific images
- Tracks all changes and provides detailed reports

Components:
- ImageReviewer: Analyzes outputs and makes refinement decisions
- ParameterOptimizer: Suggests and applies parameter adjustments
- RefinementTracker: Records all changes and generates reports
- AdaptiveExecutor: Orchestrates the refinement loop
"""

from nanorange.agent.refinement.image_reviewer import ImageReviewer
from nanorange.agent.refinement.parameter_optimizer import ParameterOptimizer
from nanorange.agent.refinement.refinement_tracker import RefinementTracker
from nanorange.agent.refinement.adaptive_executor import AdaptiveExecutor

__all__ = [
    "ImageReviewer",
    "ParameterOptimizer", 
    "RefinementTracker",
    "AdaptiveExecutor",
]
