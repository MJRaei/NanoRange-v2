"""
Schemas for iterative refinement system.

Defines data structures for:
- Tracking parameter changes
- Recording refinement decisions
- Reporting tool modifications
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RefinementAction(str, Enum):
    """Actions that can be taken after reviewing output."""
    
    ACCEPT = "accept"           # Output is good, continue to next step
    ADJUST_PARAMS = "adjust"    # Re-run with adjusted parameters
    REMOVE_TOOL = "remove"      # Remove tool from pipeline
    ADD_TOOL = "add"            # Add a new tool before/after
    REPLACE_TOOL = "replace"    # Replace with different tool
    FAIL = "fail"               # Cannot improve, mark as failed


class QualityScore(str, Enum):
    """Quality assessment levels for outputs."""
    
    EXCELLENT = "excellent"     # Perfect output, no changes needed
    GOOD = "good"               # Acceptable output, minor improvements possible
    FAIR = "fair"               # Usable but could be better
    POOR = "poor"               # Needs significant improvement
    UNUSABLE = "unusable"       # Output is not usable


class ParameterChange(BaseModel):
    """Records a single parameter change."""
    
    parameter_name: str = Field(..., description="Name of the parameter")
    old_value: Any = Field(..., description="Previous value")
    new_value: Any = Field(..., description="New value")
    reason: str = Field("", description="Why this change was made")
    
    model_config = {"extra": "forbid"}


class RefinementDecision(BaseModel):
    """
    Decision made by the image reviewer about a step's output.
    
    Contains assessment, recommended action, and suggested changes.
    """
    
    step_id: str = Field(..., description="ID of the step being reviewed")
    tool_id: str = Field(..., description="Tool that was executed")
    iteration: int = Field(1, description="Current iteration number")
    
    # Assessment
    quality_score: QualityScore = Field(..., description="Quality assessment")
    assessment: str = Field(..., description="Detailed assessment of the output")
    
    # Decision
    action: RefinementAction = Field(..., description="Recommended action")
    confidence: float = Field(
        0.8,
        description="Confidence in decision (0-1)",
        ge=0.0,
        le=1.0
    )
    
    # Suggested changes (for ADJUST_PARAMS action)
    parameter_changes: List[ParameterChange] = Field(
        default_factory=list,
        description="Suggested parameter adjustments"
    )
    
    # For ADD/REPLACE actions
    suggested_tool_id: Optional[str] = Field(
        None,
        description="Tool to add or use as replacement"
    )
    suggested_position: Optional[str] = Field(
        None,
        description="Position for new tool: 'before' or 'after'"
    )
    
    # Reasoning
    reasoning: str = Field("", description="Explanation of the decision")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"extra": "forbid"}


class StepIteration(BaseModel):
    """Records a single iteration of a step execution."""
    
    iteration: int = Field(..., description="Iteration number (1-based)")
    inputs_used: Dict[str, Any] = Field(
        default_factory=dict,
        description="Inputs used for this iteration"
    )
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Outputs from this iteration"
    )
    decision: Optional[RefinementDecision] = Field(
        None,
        description="Review decision for this iteration"
    )
    duration_seconds: Optional[float] = Field(None)
    error: Optional[str] = Field(None)
    
    model_config = {"extra": "forbid"}


class ToolModification(BaseModel):
    """Records a modification to the pipeline structure."""
    
    modification_type: str = Field(
        ...,
        description="Type: 'added', 'removed', 'replaced'"
    )
    step_id: str = Field(..., description="Step ID affected")
    tool_id: str = Field(..., description="Tool that was modified")
    
    # For replacements
    replaced_by: Optional[str] = Field(
        None,
        description="New tool ID if replaced"
    )
    
    # Context
    reason: str = Field(..., description="Why this modification was made")
    triggered_by_step: Optional[str] = Field(
        None,
        description="Which step's output triggered this"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"extra": "forbid"}


class StepRefinementHistory(BaseModel):
    """Complete refinement history for a single step."""
    
    step_id: str = Field(..., description="Step ID")
    step_name: str = Field(..., description="Human-readable step name")
    tool_id: str = Field(..., description="Tool used")
    
    # Track if user provided strict values
    user_locked_params: List[str] = Field(
        default_factory=list,
        description="Parameters with user-specified values (not to be changed)"
    )
    
    # Iteration history
    iterations: List[StepIteration] = Field(
        default_factory=list,
        description="All iterations attempted"
    )
    
    # Final outcome
    final_iteration: Optional[int] = Field(None, description="Which iteration was accepted")
    was_removed: bool = Field(False, description="Whether step was removed from pipeline")
    removal_reason: Optional[str] = Field(None)
    
    @property
    def total_iterations(self) -> int:
        """Total number of iterations attempted."""
        return len(self.iterations)
    
    @property
    def had_refinements(self) -> bool:
        """Whether any refinements were made."""
        return len(self.iterations) > 1 or self.was_removed
    
    model_config = {"extra": "forbid"}


class RefinementReport(BaseModel):
    """
    Complete report of all refinements made during pipeline execution.
    
    Provides a detailed summary of:
    - All parameter changes made
    - Tools that were removed or added
    - Iteration history for each step
    """
    
    pipeline_id: str = Field(..., description="Pipeline ID")
    pipeline_name: str = Field(..., description="Pipeline name")
    
    # Overall stats
    total_steps_executed: int = Field(0)
    total_iterations: int = Field(0)
    steps_refined: int = Field(0, description="Steps that needed refinement")
    tools_removed: int = Field(0)
    tools_added: int = Field(0)
    
    # Detailed history per step
    step_histories: Dict[str, StepRefinementHistory] = Field(
        default_factory=dict,
        description="Refinement history keyed by step_id"
    )
    
    # Pipeline-level modifications
    pipeline_modifications: List[ToolModification] = Field(
        default_factory=list,
        description="All pipeline structure changes"
    )
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    
    model_config = {"extra": "forbid"}
    
    def add_step_history(self, history: StepRefinementHistory) -> None:
        """Add or update step history."""
        self.step_histories[history.step_id] = history
        if history.had_refinements:
            self.steps_refined += 1
        if history.was_removed:
            self.tools_removed += 1
    
    def add_modification(self, mod: ToolModification) -> None:
        """Record a pipeline modification."""
        self.pipeline_modifications.append(mod)
        if mod.modification_type == "added":
            self.tools_added += 1
        elif mod.modification_type == "removed":
            self.tools_removed += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary of refinements."""
        changes = []
        
        for step_id, history in self.step_histories.items():
            if not history.had_refinements:
                continue
            
            step_changes = {
                "step": history.step_name,
                "tool": history.tool_id,
                "iterations": history.total_iterations,
                "parameter_changes": [],
            }
            
            # Collect parameter changes across iterations
            for iteration in history.iterations:
                if iteration.decision and iteration.decision.parameter_changes:
                    for change in iteration.decision.parameter_changes:
                        step_changes["parameter_changes"].append({
                            "param": change.parameter_name,
                            "from": change.old_value,
                            "to": change.new_value,
                            "reason": change.reason,
                        })
            
            if history.was_removed:
                step_changes["removed"] = True
                step_changes["removal_reason"] = history.removal_reason
            
            changes.append(step_changes)
        
        return {
            "pipeline": self.pipeline_name,
            "total_iterations": self.total_iterations,
            "steps_refined": self.steps_refined,
            "tools_removed": self.tools_removed,
            "tools_added": self.tools_added,
            "duration_seconds": self.total_duration_seconds,
            "step_changes": changes,
            "pipeline_modifications": [
                {
                    "type": m.modification_type,
                    "tool": m.tool_id,
                    "reason": m.reason,
                }
                for m in self.pipeline_modifications
            ],
        }
