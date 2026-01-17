"""
Refinement Tracker - Records and reports all refinement activities.

Maintains a detailed history of:
- All iterations for each step
- Parameter changes made
- Pipeline modifications (tools added/removed)
- Final outcomes
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from nanorange.core.refinement_schemas import (
    RefinementReport,
    StepRefinementHistory,
    StepIteration,
    ToolModification,
    RefinementDecision,
    ParameterChange,
)


class RefinementTracker:
    """
    Tracks all refinement activities during pipeline execution.
    
    Provides:
    - Real-time tracking of iterations and changes
    - Generation of detailed reports
    - Human-readable summaries
    """
    
    def __init__(self, pipeline_id: str, pipeline_name: str):
        """
        Initialize the tracker.
        
        Args:
            pipeline_id: Pipeline being executed
            pipeline_name: Human-readable pipeline name
        """
        self.report = RefinementReport(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name
        )
        self._current_step_history: Optional[StepRefinementHistory] = None
    
    def start_execution(self) -> None:
        """Mark the start of pipeline execution."""
        self.report.started_at = datetime.utcnow()
    
    def end_execution(self) -> None:
        """Mark the end of pipeline execution."""
        self.report.completed_at = datetime.utcnow()
        if self.report.started_at:
            self.report.total_duration_seconds = (
                self.report.completed_at - self.report.started_at
            ).total_seconds()
    
    def start_step(
        self,
        step_id: str,
        step_name: str,
        tool_id: str,
        user_locked_params: List[str]
    ) -> None:
        """
        Start tracking a new step.
        
        Args:
            step_id: Step ID
            step_name: Human-readable name
            tool_id: Tool being used
            user_locked_params: Parameters that shouldn't be changed
        """
        self._current_step_history = StepRefinementHistory(
            step_id=step_id,
            step_name=step_name,
            tool_id=tool_id,
            user_locked_params=user_locked_params
        )
        self.report.total_steps_executed += 1
    
    def record_iteration(
        self,
        iteration: int,
        inputs_used: Dict[str, Any],
        outputs: Dict[str, Any],
        decision: Optional[RefinementDecision] = None,
        duration_seconds: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Record an iteration of step execution.
        
        Args:
            iteration: Iteration number
            inputs_used: Parameters used
            outputs: Tool outputs
            decision: Refinement decision if reviewed
            duration_seconds: Execution time
            error: Error message if failed
        """
        if not self._current_step_history:
            return
        
        step_iter = StepIteration(
            iteration=iteration,
            inputs_used=inputs_used.copy(),
            outputs=outputs.copy() if outputs else {},
            decision=decision,
            duration_seconds=duration_seconds,
            error=error
        )
        
        self._current_step_history.iterations.append(step_iter)
        self.report.total_iterations += 1
    
    def finalize_step(
        self,
        accepted_iteration: Optional[int] = None,
        was_removed: bool = False,
        removal_reason: Optional[str] = None
    ) -> None:
        """
        Finalize tracking for the current step.
        
        Args:
            accepted_iteration: Which iteration was accepted
            was_removed: Whether the step was removed
            removal_reason: Why it was removed
        """
        if not self._current_step_history:
            return
        
        self._current_step_history.final_iteration = accepted_iteration
        self._current_step_history.was_removed = was_removed
        self._current_step_history.removal_reason = removal_reason
        
        self.report.add_step_history(self._current_step_history)
        self._current_step_history = None
    
    def record_tool_removal(
        self,
        step_id: str,
        tool_id: str,
        reason: str,
        triggered_by_step: Optional[str] = None
    ) -> None:
        """
        Record a tool being removed from the pipeline.
        
        Args:
            step_id: Step that was removed
            tool_id: Tool that was in the step
            reason: Why it was removed
            triggered_by_step: Which step's output triggered removal
        """
        modification = ToolModification(
            modification_type="removed",
            step_id=step_id,
            tool_id=tool_id,
            reason=reason,
            triggered_by_step=triggered_by_step
        )
        self.report.add_modification(modification)
    
    def record_tool_addition(
        self,
        step_id: str,
        tool_id: str,
        reason: str,
        triggered_by_step: Optional[str] = None
    ) -> None:
        """
        Record a tool being added to the pipeline.
        
        Args:
            step_id: New step ID
            tool_id: Tool being added
            reason: Why it was added
            triggered_by_step: Which step's output triggered addition
        """
        modification = ToolModification(
            modification_type="added",
            step_id=step_id,
            tool_id=tool_id,
            reason=reason,
            triggered_by_step=triggered_by_step
        )
        self.report.add_modification(modification)
    
    def record_tool_replacement(
        self,
        step_id: str,
        old_tool_id: str,
        new_tool_id: str,
        reason: str
    ) -> None:
        """
        Record a tool being replaced with another.
        
        Args:
            step_id: Step being modified
            old_tool_id: Original tool
            new_tool_id: Replacement tool
            reason: Why it was replaced
        """
        modification = ToolModification(
            modification_type="replaced",
            step_id=step_id,
            tool_id=old_tool_id,
            replaced_by=new_tool_id,
            reason=reason
        )
        self.report.add_modification(modification)
    
    def get_report(self) -> RefinementReport:
        """Get the complete refinement report."""
        return self.report
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a human-readable summary."""
        return self.report.get_summary()
    
    def get_step_changes_description(self) -> str:
        """
        Generate a human-readable description of all changes.
        
        Returns:
            Formatted string describing all refinements
        """
        lines = [
            f"# Refinement Report: {self.report.pipeline_name}",
            "",
            f"Total Steps: {self.report.total_steps_executed}",
            f"Total Iterations: {self.report.total_iterations}",
            f"Steps Refined: {self.report.steps_refined}",
            f"Tools Removed: {self.report.tools_removed}",
            f"Tools Added: {self.report.tools_added}",
            "",
        ]
        
        # Detail each step that had changes
        for step_id, history in self.report.step_histories.items():
            if not history.had_refinements:
                continue
            
            lines.append(f"## Step: {history.step_name} ({history.tool_id})")
            lines.append(f"   Iterations: {history.total_iterations}")
            
            if history.was_removed:
                lines.append(f"   REMOVED: {history.removal_reason}")
            
            # Show parameter changes
            all_changes = []
            for iteration in history.iterations:
                if iteration.decision and iteration.decision.parameter_changes:
                    for change in iteration.decision.parameter_changes:
                        all_changes.append(
                            f"     - {change.parameter_name}: "
                            f"{change.old_value} -> {change.new_value} "
                            f"({change.reason})"
                        )
            
            if all_changes:
                lines.append("   Parameter Changes:")
                lines.extend(all_changes)
            
            lines.append("")
        
        # Show pipeline modifications
        if self.report.pipeline_modifications:
            lines.append("## Pipeline Modifications")
            for mod in self.report.pipeline_modifications:
                if mod.modification_type == "removed":
                    lines.append(f"   - Removed: {mod.tool_id} - {mod.reason}")
                elif mod.modification_type == "added":
                    lines.append(f"   - Added: {mod.tool_id} - {mod.reason}")
                elif mod.modification_type == "replaced":
                    lines.append(
                        f"   - Replaced: {mod.tool_id} -> {mod.replaced_by} "
                        f"- {mod.reason}"
                    )
        
        return "\n".join(lines)
    
    def get_changes_for_user(self) -> Dict[str, Any]:
        """
        Get a structured summary suitable for displaying to the user.
        
        Returns:
            Dictionary with user-friendly change information
        """
        changes = {
            "summary": {
                "total_iterations": self.report.total_iterations,
                "steps_refined": self.report.steps_refined,
                "tools_removed": self.report.tools_removed,
                "tools_added": self.report.tools_added,
            },
            "step_details": [],
            "pipeline_changes": []
        }
        
        for step_id, history in self.report.step_histories.items():
            step_info = {
                "step_name": history.step_name,
                "tool": history.tool_id,
                "iterations": history.total_iterations,
                "was_removed": history.was_removed,
                "removal_reason": history.removal_reason,
                "parameter_adjustments": []
            }
            
            for iteration in history.iterations:
                if iteration.decision and iteration.decision.parameter_changes:
                    for change in iteration.decision.parameter_changes:
                        step_info["parameter_adjustments"].append({
                            "parameter": change.parameter_name,
                            "from_value": change.old_value,
                            "to_value": change.new_value,
                            "reason": change.reason
                        })
            
            if history.had_refinements or history.was_removed:
                changes["step_details"].append(step_info)
        
        for mod in self.report.pipeline_modifications:
            changes["pipeline_changes"].append({
                "type": mod.modification_type,
                "tool": mod.tool_id,
                "replaced_by": mod.replaced_by,
                "reason": mod.reason
            })
        
        return changes
