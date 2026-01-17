"""
Parameter Optimizer - Applies and validates parameter adjustments.

Handles the logic of applying suggested parameter changes while respecting
user-specified constraints and tool parameter bounds.
"""

from typing import Any, Dict, List, Optional, Tuple

from nanorange.core.schemas import ToolSchema, InputSchema, DataType
from nanorange.core.refinement_schemas import ParameterChange, RefinementDecision


class ParameterOptimizer:
    """
    Handles parameter adjustment and validation.
    
    Responsibilities:
    - Validate suggested parameter changes
    - Apply changes while respecting constraints
    - Track which parameters are user-locked
    - Suggest fallback values when suggestions are invalid
    """
    
    def __init__(self):
        """Initialize the parameter optimizer."""
        self._adjustment_history: Dict[str, List[Dict]] = {}
    
    def identify_locked_params(
        self,
        inputs_provided: Dict[str, Any],
        tool_schema: ToolSchema
    ) -> List[str]:
        """
        Identify which parameters were explicitly provided by the user.
        
        Parameters that the user explicitly set (not defaults) should not
        be changed during refinement.
        
        Args:
            inputs_provided: The inputs provided for the step
            tool_schema: The tool's schema
            
        Returns:
            List of parameter names that should not be modified
        """
        locked = []
        
        for param_name, value in inputs_provided.items():
            # Get the schema for this input
            input_schema = tool_schema.get_input(param_name)
            if not input_schema:
                continue
            
            # If input is required and has no default, user must have provided it
            if input_schema.required and input_schema.default is None:
                locked.append(param_name)
                continue
            
            # If value differs from default, user provided it explicitly
            if input_schema.default is not None and value != input_schema.default:
                # Check if it looks like a user-specified value
                # Numbers that are "nice" values might be user-specified
                if isinstance(value, (int, float)):
                    if self._is_likely_user_specified(value, input_schema):
                        locked.append(param_name)
        
        return locked
    
    def _is_likely_user_specified(
        self,
        value: Any,
        input_schema: InputSchema
    ) -> bool:
        """
        Heuristic to determine if a numeric value was likely user-specified.
        
        User-specified values tend to be "round" numbers like 10, 50, 100, 0.5, etc.
        """
        if not isinstance(value, (int, float)):
            return True
        
        # Check if it's a "round" number
        if isinstance(value, int):
            # Integers divisible by 5 or 10 are likely user-specified
            if value % 5 == 0 or value % 10 == 0:
                return True
        
        if isinstance(value, float):
            # Check for common user-friendly values
            common_floats = {0.1, 0.2, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0}
            if value in common_floats:
                return True
            # Check if it has few decimal places
            str_val = str(value)
            if '.' in str_val and len(str_val.split('.')[1]) <= 2:
                return True
        
        return False
    
    def validate_change(
        self,
        change: ParameterChange,
        tool_schema: ToolSchema,
        locked_params: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate a proposed parameter change.
        
        Args:
            change: The proposed change
            tool_schema: Tool schema for validation
            locked_params: Parameters that cannot be changed
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if parameter is locked
        if change.parameter_name in locked_params:
            return False, f"Parameter '{change.parameter_name}' is user-specified and cannot be changed"
        
        # Get input schema
        input_schema = tool_schema.get_input(change.parameter_name)
        if not input_schema:
            return False, f"Unknown parameter: {change.parameter_name}"
        
        new_value = change.new_value
        
        # Validate by type
        if input_schema.type == DataType.INT:
            if not isinstance(new_value, (int, float)):
                return False, f"Parameter {change.parameter_name} requires integer value"
            new_value = int(new_value)
        
        elif input_schema.type == DataType.FLOAT:
            if not isinstance(new_value, (int, float)):
                return False, f"Parameter {change.parameter_name} requires numeric value"
            new_value = float(new_value)
        
        # Check bounds
        if input_schema.min_value is not None and new_value < input_schema.min_value:
            return False, f"Value {new_value} below minimum {input_schema.min_value}"
        
        if input_schema.max_value is not None and new_value > input_schema.max_value:
            return False, f"Value {new_value} above maximum {input_schema.max_value}"
        
        # Check choices
        if input_schema.choices and str(new_value) not in input_schema.choices:
            return False, f"Value {new_value} not in allowed choices: {input_schema.choices}"
        
        return True, ""
    
    def apply_changes(
        self,
        current_inputs: Dict[str, Any],
        decision: RefinementDecision,
        tool_schema: ToolSchema,
        locked_params: List[str]
    ) -> Tuple[Dict[str, Any], List[ParameterChange]]:
        """
        Apply validated parameter changes to inputs.
        
        Args:
            current_inputs: Current input values
            decision: Refinement decision with suggested changes
            tool_schema: Tool schema for validation
            locked_params: Parameters that cannot be changed
            
        Returns:
            Tuple of (new_inputs, applied_changes)
        """
        new_inputs = current_inputs.copy()
        applied_changes = []
        
        for change in decision.parameter_changes:
            is_valid, error = self.validate_change(change, tool_schema, locked_params)
            
            if not is_valid:
                continue
            
            # Apply the change
            input_schema = tool_schema.get_input(change.parameter_name)
            new_value = change.new_value
            
            # Type conversion
            if input_schema.type == DataType.INT:
                new_value = int(new_value)
            elif input_schema.type == DataType.FLOAT:
                new_value = float(new_value)
            elif input_schema.type == DataType.BOOL:
                new_value = bool(new_value)
            
            # Store original and apply
            applied_change = ParameterChange(
                parameter_name=change.parameter_name,
                old_value=current_inputs.get(change.parameter_name),
                new_value=new_value,
                reason=change.reason
            )
            
            new_inputs[change.parameter_name] = new_value
            applied_changes.append(applied_change)
            
            # Track in history
            self._track_adjustment(
                decision.step_id,
                change.parameter_name,
                current_inputs.get(change.parameter_name),
                new_value
            )
        
        return new_inputs, applied_changes
    
    def _track_adjustment(
        self,
        step_id: str,
        param_name: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Track parameter adjustment for history."""
        if step_id not in self._adjustment_history:
            self._adjustment_history[step_id] = []
        
        self._adjustment_history[step_id].append({
            "parameter": param_name,
            "from": old_value,
            "to": new_value
        })
    
    def get_adjustment_history(self, step_id: str) -> List[Dict]:
        """Get adjustment history for a step."""
        return self._adjustment_history.get(step_id, [])
    
    def suggest_alternative_values(
        self,
        param_name: str,
        current_value: Any,
        input_schema: InputSchema,
        iteration: int
    ) -> Optional[Any]:
        """
        Suggest an alternative value when the model's suggestion is invalid.
        
        This provides fallback suggestions based on parameter type and bounds.
        
        Args:
            param_name: Parameter name
            current_value: Current value
            input_schema: Input schema
            iteration: Current iteration (affects suggestion strategy)
            
        Returns:
            Suggested value or None
        """
        if input_schema.choices:
            # Try next choice in list
            choices = input_schema.choices
            if str(current_value) in choices:
                idx = choices.index(str(current_value))
                next_idx = (idx + 1) % len(choices)
                return choices[next_idx]
            return choices[0]
        
        if input_schema.type in (DataType.INT, DataType.FLOAT):
            return self._suggest_numeric_alternative(
                current_value,
                input_schema,
                iteration
            )
        
        return None
    
    def _suggest_numeric_alternative(
        self,
        current_value: Any,
        input_schema: InputSchema,
        iteration: int
    ) -> Optional[Any]:
        """Suggest alternative numeric value."""
        min_val = input_schema.min_value
        max_val = input_schema.max_value
        
        if min_val is None:
            min_val = 0
        if max_val is None:
            max_val = current_value * 3 if current_value else 255
        
        value_range = max_val - min_val
        
        # Strategy: explore the parameter space
        if iteration == 1:
            # Try increasing by 20%
            new_val = current_value * 1.2
        elif iteration == 2:
            # Try decreasing by 20%
            new_val = current_value * 0.8
        else:
            # Try middle of remaining range
            if current_value > (min_val + max_val) / 2:
                new_val = (min_val + current_value) / 2
            else:
                new_val = (current_value + max_val) / 2
        
        # Ensure within bounds
        new_val = max(min_val, min(max_val, new_val))
        
        # Type conversion
        if input_schema.type == DataType.INT:
            return int(new_val)
        return float(new_val)
