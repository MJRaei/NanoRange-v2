"""
Pipeline Validator - Validates pipeline definitions before execution.

Checks for:
- Valid tool references
- Type compatibility between connected steps
- Cycle detection (DAG validation)
- Required inputs are satisfied
"""

from typing import Dict, List, Optional, Set, Tuple
from nanorange.core.schemas import (
    DataType,
    InputSource,
    Pipeline,
    PipelineStep,
    StepInput,
    ToolSchema,
)
from nanorange.core.registry import ToolRegistry, get_registry


class ValidationError:
    """Represents a single validation error."""
    
    def __init__(
        self,
        message: str,
        step_id: Optional[str] = None,
        field: Optional[str] = None,
        severity: str = "error"
    ):
        self.message = message
        self.step_id = step_id
        self.field = field
        self.severity = severity  # "error" or "warning"
    
    def __str__(self) -> str:
        parts = []
        if self.step_id:
            parts.append(f"[Step: {self.step_id}]")
        if self.field:
            parts.append(f"[{self.field}]")
        parts.append(self.message)
        return " ".join(parts)


class ValidationResult:
    """Result of pipeline validation."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    @property
    def is_valid(self) -> bool:
        """Pipeline is valid if there are no errors."""
        return len(self.errors) == 0
    
    def add_error(
        self,
        message: str,
        step_id: Optional[str] = None,
        field: Optional[str] = None
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(message, step_id, field, "error"))
    
    def add_warning(
        self,
        message: str,
        step_id: Optional[str] = None,
        field: Optional[str] = None
    ) -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationError(message, step_id, field, "warning"))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [str(e) for e in self.errors],
            "warnings": [str(w) for w in self.warnings],
        }
    
    def __str__(self) -> str:
        lines = []
        if self.errors:
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  - {e}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        if self.is_valid:
            lines.append("Pipeline is valid.")
        return "\n".join(lines)


class PipelineValidator:
    """Validates pipeline definitions."""
    
    # Types that are compatible (can be connected)
    # Key = target input type, Value = set of source output types it can accept
    TYPE_COMPATIBILITY: Dict[DataType, Set[DataType]] = {
        DataType.IMAGE: {DataType.IMAGE, DataType.PATH, DataType.MASK},  # Mask is a binary image
        DataType.MASK: {DataType.MASK, DataType.IMAGE, DataType.PATH},
        DataType.PATH: {DataType.PATH, DataType.IMAGE, DataType.MASK, DataType.STRING},
        DataType.ARRAY: {DataType.ARRAY},
        DataType.FLOAT: {DataType.FLOAT, DataType.INT},
        DataType.INT: {DataType.INT},
        DataType.STRING: {DataType.STRING, DataType.PATH},
        DataType.BOOL: {DataType.BOOL},
        DataType.LIST: {DataType.LIST},
        DataType.DICT: {DataType.DICT, DataType.PARAMETERS, DataType.MEASUREMENTS},
        DataType.MEASUREMENTS: {DataType.MEASUREMENTS, DataType.DICT},
        DataType.PARAMETERS: {DataType.PARAMETERS, DataType.DICT},
        DataType.INSTRUCTIONS: {DataType.INSTRUCTIONS, DataType.STRING},
    }
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Initialize validator.
        
        Args:
            registry: Tool registry to use (defaults to global)
        """
        self.registry = registry or get_registry()
    
    def validate(self, pipeline: Pipeline) -> ValidationResult:
        """
        Validate a pipeline definition.
        
        Args:
            pipeline: The pipeline to validate
            
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        
        # Basic structure validation
        self._validate_structure(pipeline, result)
        
        if result.errors:
            return result  # Stop early if structure is invalid
        
        # Tool reference validation
        self._validate_tool_references(pipeline, result)
        
        # Input validation
        self._validate_inputs(pipeline, result)
        
        # Type compatibility validation
        self._validate_type_compatibility(pipeline, result)
        
        # Cycle detection
        self._validate_no_cycles(pipeline, result)
        
        return result
    
    def _validate_structure(
        self,
        pipeline: Pipeline,
        result: ValidationResult
    ) -> None:
        """Validate basic pipeline structure."""
        if not pipeline.steps:
            result.add_warning("Pipeline has no steps")
            return
        
        # Check for duplicate step IDs
        seen_ids: Set[str] = set()
        seen_names: Set[str] = set()
        
        for step in pipeline.steps:
            if step.step_id in seen_ids:
                result.add_error(
                    f"Duplicate step ID: {step.step_id}",
                    step_id=step.step_id
                )
            seen_ids.add(step.step_id)
            
            if step.step_name in seen_names:
                result.add_warning(
                    f"Duplicate step name: {step.step_name}",
                    step_id=step.step_id
                )
            seen_names.add(step.step_name)
    
    def _validate_tool_references(
        self,
        pipeline: Pipeline,
        result: ValidationResult
    ) -> None:
        """Validate that all referenced tools exist."""
        for step in pipeline.steps:
            if not self.registry.has_tool(step.tool_id):
                result.add_error(
                    f"Unknown tool: {step.tool_id}",
                    step_id=step.step_id,
                    field="tool_id"
                )
    
    def _validate_inputs(
        self,
        pipeline: Pipeline,
        result: ValidationResult
    ) -> None:
        """Validate that required inputs are provided."""
        step_ids = {step.step_id for step in pipeline.steps}
        
        for step in pipeline.steps:
            schema = self.registry.get_schema(step.tool_id)
            if not schema:
                continue  # Already reported in tool reference validation
            
            # Check required inputs
            for inp in schema.inputs:
                if inp.name not in step.inputs:
                    if inp.required:
                        result.add_error(
                            f"Missing required input: {inp.name}",
                            step_id=step.step_id,
                            field=f"inputs.{inp.name}"
                        )
                else:
                    # Validate the input source
                    step_input = step.inputs[inp.name]
                    self._validate_input_source(
                        step, step_input, inp.name, step_ids, result
                    )
    
    def _validate_input_source(
        self,
        step: PipelineStep,
        step_input: StepInput,
        input_name: str,
        step_ids: Set[str],
        result: ValidationResult
    ) -> None:
        """Validate a single input source."""
        if step_input.source == InputSource.STEP_OUTPUT:
            # Check source step exists
            if not step_input.source_step_id:
                result.add_error(
                    f"Input '{input_name}' has no source_step_id",
                    step_id=step.step_id,
                    field=f"inputs.{input_name}"
                )
            elif step_input.source_step_id not in step_ids:
                result.add_error(
                    f"Input '{input_name}' references unknown step: {step_input.source_step_id}",
                    step_id=step.step_id,
                    field=f"inputs.{input_name}"
                )
            
            if not step_input.source_output:
                result.add_error(
                    f"Input '{input_name}' has no source_output",
                    step_id=step.step_id,
                    field=f"inputs.{input_name}"
                )
        
        elif step_input.source == InputSource.STATIC:
            if step_input.value is None:
                # Could be intentional, just warn
                result.add_warning(
                    f"Input '{input_name}' has null static value",
                    step_id=step.step_id,
                    field=f"inputs.{input_name}"
                )
    
    def _validate_type_compatibility(
        self,
        pipeline: Pipeline,
        result: ValidationResult
    ) -> None:
        """Validate type compatibility between connected steps."""
        for step in pipeline.steps:
            schema = self.registry.get_schema(step.tool_id)
            if not schema:
                continue
            
            for input_name, step_input in step.inputs.items():
                if step_input.source != InputSource.STEP_OUTPUT:
                    continue
                
                # Get input type
                input_schema = schema.get_input(input_name)
                if not input_schema:
                    result.add_error(
                        f"Unknown input: {input_name}",
                        step_id=step.step_id,
                        field=f"inputs.{input_name}"
                    )
                    continue
                
                # Get source output type
                source_step = pipeline.get_step(step_input.source_step_id)
                if not source_step:
                    continue  # Already reported
                
                source_schema = self.registry.get_schema(source_step.tool_id)
                if not source_schema:
                    continue
                
                output_schema = source_schema.get_output(step_input.source_output)
                if not output_schema:
                    result.add_error(
                        f"Source step '{source_step.step_name}' has no output '{step_input.source_output}'",
                        step_id=step.step_id,
                        field=f"inputs.{input_name}"
                    )
                    continue
                
                # Check type compatibility
                if not self._types_compatible(
                    output_schema.type, input_schema.type
                ):
                    result.add_error(
                        f"Type mismatch: {output_schema.type.value} -> {input_schema.type.value}",
                        step_id=step.step_id,
                        field=f"inputs.{input_name}"
                    )
    
    def _types_compatible(
        self,
        source_type: DataType,
        target_type: DataType
    ) -> bool:
        """Check if two types are compatible for connection."""
        if source_type == target_type:
            return True
        
        compatible_types = self.TYPE_COMPATIBILITY.get(target_type, set())
        return source_type in compatible_types
    
    def _validate_no_cycles(
        self,
        pipeline: Pipeline,
        result: ValidationResult
    ) -> None:
        """Detect cycles in the pipeline graph."""
        # Build adjacency list
        graph: Dict[str, List[str]] = {step.step_id: [] for step in pipeline.steps}
        
        for step in pipeline.steps:
            for step_input in step.inputs.values():
                if step_input.source == InputSource.STEP_OUTPUT:
                    if step_input.source_step_id:
                        graph[step_input.source_step_id].append(step.step_id)
        
        # DFS to detect cycles
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for step_id in graph:
            if step_id not in visited:
                if has_cycle(step_id):
                    result.add_error(
                        "Pipeline contains a cycle (circular dependency)"
                    )
                    return
    
    def get_execution_order(self, pipeline: Pipeline) -> List[str]:
        """
        Get topologically sorted step IDs for execution order.
        
        Args:
            pipeline: Validated pipeline
            
        Returns:
            List of step IDs in execution order
            
        Raises:
            ValueError: If pipeline has cycles
        """
        # Build adjacency list and in-degree count
        graph: Dict[str, List[str]] = {step.step_id: [] for step in pipeline.steps}
        in_degree: Dict[str, int] = {step.step_id: 0 for step in pipeline.steps}
        
        for step in pipeline.steps:
            for step_input in step.inputs.values():
                if step_input.source == InputSource.STEP_OUTPUT:
                    if step_input.source_step_id:
                        graph[step_input.source_step_id].append(step.step_id)
                        in_degree[step.step_id] += 1
        
        # Kahn's algorithm for topological sort
        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        order = []
        
        while queue:
            node = queue.pop(0)
            order.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(order) != len(pipeline.steps):
            raise ValueError("Pipeline contains a cycle")
        
        return order
