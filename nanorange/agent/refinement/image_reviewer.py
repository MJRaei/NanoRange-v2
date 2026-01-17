"""
Image Reviewer - Analyzes tool outputs and makes refinement decisions.

Uses a vision model to assess output quality and suggest improvements.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from nanorange.core.schemas import ToolSchema, InputSchema
from nanorange.core.refinement_schemas import (
    RefinementDecision,
    RefinementAction,
    QualityScore,
    ParameterChange,
)
from nanorange import settings


class ImageReviewer:
    """
    Reviews image outputs and decides if refinement is needed.
    
    Uses a vision-capable LLM to:
    - Assess output quality
    - Identify issues (noise, artifacts, missed objects, etc.)
    - Suggest parameter adjustments
    - Recommend tool changes if needed
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        max_iterations: Optional[int] = None
    ):
        """
        Initialize the image reviewer.
        
        Args:
            model_name: Vision model to use (defaults to settings.IMAGE_REVIEWER_MODEL)
            max_iterations: Max iterations per tool (defaults to settings.MAX_TOOL_ITERATIONS)
        """
        self.model_name = model_name or settings.IMAGE_REVIEWER_MODEL
        self.max_iterations = max_iterations or settings.MAX_TOOL_ITERATIONS
        self._client = None
    
    def _get_client(self):
        """Lazy-load the Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._client
    
    def _load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load an image file as PIL Image."""
        path = Path(image_path)
        if not path.exists():
            return None
        
        try:
            img = Image.open(path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception:
            return None
    
    def _build_review_prompt(
        self,
        tool_schema: ToolSchema,
        inputs_used: Dict[str, Any],
        user_locked_params: List[str],
        iteration: int,
        context: Optional[str] = None
    ) -> str:
        """Build the prompt for the image reviewer."""
        
        # Build parameter info
        param_info = []
        adjustable_params = []
        
        for inp in tool_schema.inputs:
            current_val = inputs_used.get(inp.name, inp.default)
            is_locked = inp.name in user_locked_params
            
            param_line = f"- {inp.name}: {current_val}"
            if is_locked:
                param_line += " [USER-SPECIFIED - DO NOT CHANGE]"
            else:
                param_line += f" (type: {inp.type.value}"
                if inp.min_value is not None:
                    param_line += f", min: {inp.min_value}"
                if inp.max_value is not None:
                    param_line += f", max: {inp.max_value}"
                if inp.choices:
                    param_line += f", choices: {inp.choices}"
                param_line += ")"
                adjustable_params.append(inp)
            
            param_info.append(param_line)
        
        prompt = f"""You are an expert image analysis reviewer. Analyze this output image from the "{tool_schema.name}" tool.

## Tool Information
- Tool: {tool_schema.name}
- Description: {tool_schema.description}
- Purpose: {context or "Image processing/analysis"}

## Current Parameters Used
{chr(10).join(param_info)}

## Your Task
Evaluate the output image quality and decide the next action.

Iteration: {iteration} of {self.max_iterations}

## Response Format (JSON)
Respond with ONLY a valid JSON object:
{{
    "quality_score": "excellent|good|fair|poor|unusable",
    "assessment": "Detailed description of what you observe in the output",
    "action": "accept|adjust|remove|fail",
    "reasoning": "Why you chose this action",
    "parameter_changes": [
        {{
            "parameter_name": "name",
            "new_value": value,
            "reason": "why this change"
        }}
    ]
}}

## Guidelines
- "accept": Output quality is sufficient for the next step
- "adjust": Output can be improved by changing parameters (only if iteration < {self.max_iterations})
- "remove": This tool is not appropriate for this image, remove from pipeline
- "fail": Cannot achieve acceptable results, stop refinement

IMPORTANT:
- Only suggest changes to parameters NOT marked [USER-SPECIFIED]
- Parameter values must be within their valid ranges
- If iteration = {self.max_iterations} and quality is still poor, choose "accept" or "remove"
"""
        
        return prompt
    
    def review_output(
        self,
        step_id: str,
        tool_schema: ToolSchema,
        output_image_path: str,
        inputs_used: Dict[str, Any],
        user_locked_params: List[str],
        iteration: int,
        input_image_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> RefinementDecision:
        """
        Review a tool's output image and decide on refinement.
        
        Args:
            step_id: ID of the pipeline step
            tool_schema: Schema of the tool that produced the output
            output_image_path: Path to the output image
            inputs_used: Parameters used for this execution
            user_locked_params: Parameters that should not be changed
            iteration: Current iteration number
            input_image_path: Optional path to input image for comparison
            context: Optional context about what the pipeline is trying to achieve
            
        Returns:
            RefinementDecision with assessment and recommended action
        """
        # Check if model is configured
        if not self.model_name:
            # No reviewer model configured, auto-accept
            return RefinementDecision(
                step_id=step_id,
                tool_id=tool_schema.tool_id,
                iteration=iteration,
                quality_score=QualityScore.GOOD,
                assessment="Auto-accepted (no reviewer model configured)",
                action=RefinementAction.ACCEPT,
                confidence=1.0,
                reasoning="IMAGE_REVIEWER_MODEL not configured in settings"
            )
        
        # Load output image
        output_img = self._load_image(output_image_path)
        if not output_img:
            return RefinementDecision(
                step_id=step_id,
                tool_id=tool_schema.tool_id,
                iteration=iteration,
                quality_score=QualityScore.UNUSABLE,
                assessment=f"Could not load output image: {output_image_path}",
                action=RefinementAction.FAIL,
                confidence=1.0,
                reasoning="Output image not accessible"
            )
        
        # Build prompt and images
        prompt = self._build_review_prompt(
            tool_schema=tool_schema,
            inputs_used=inputs_used,
            user_locked_params=user_locked_params,
            iteration=iteration,
            context=context
        )
        
        # Prepare content for the model (prompt + images)
        content_parts = [prompt]
        
        # Add input image if available (for comparison)
        if input_image_path:
            input_img = self._load_image(input_image_path)
            if input_img:
                content_parts.append("Input image (before processing):")
                content_parts.append(input_img)
        
        # Add output image
        content_parts.append("Output image (result to evaluate):")
        content_parts.append(output_img)
        
        try:
            # Call the vision model
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=content_parts
            )
            
            # Parse response
            return self._parse_review_response(
                step_id=step_id,
                tool_id=tool_schema.tool_id,
                iteration=iteration,
                response_text=response.text,
                inputs_used=inputs_used
            )
            
        except Exception as e:
            # On error, default to accept to continue pipeline
            return RefinementDecision(
                step_id=step_id,
                tool_id=tool_schema.tool_id,
                iteration=iteration,
                quality_score=QualityScore.FAIR,
                assessment=f"Review error: {str(e)}",
                action=RefinementAction.ACCEPT,
                confidence=0.5,
                reasoning=f"Review failed with error, defaulting to accept: {str(e)}"
            )
    
    def _parse_review_response(
        self,
        step_id: str,
        tool_id: str,
        iteration: int,
        response_text: str,
        inputs_used: Dict[str, Any]
    ) -> RefinementDecision:
        """Parse the model's JSON response into a RefinementDecision."""
        import json
        
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            # Map quality score
            quality_map = {
                "excellent": QualityScore.EXCELLENT,
                "good": QualityScore.GOOD,
                "fair": QualityScore.FAIR,
                "poor": QualityScore.POOR,
                "unusable": QualityScore.UNUSABLE,
            }
            quality = quality_map.get(
                data.get("quality_score", "fair").lower(),
                QualityScore.FAIR
            )
            
            # Map action
            action_map = {
                "accept": RefinementAction.ACCEPT,
                "adjust": RefinementAction.ADJUST_PARAMS,
                "remove": RefinementAction.REMOVE_TOOL,
                "fail": RefinementAction.FAIL,
            }
            action = action_map.get(
                data.get("action", "accept").lower(),
                RefinementAction.ACCEPT
            )
            
            # Parse parameter changes
            param_changes = []
            for change in data.get("parameter_changes", []):
                param_name = change.get("parameter_name")
                if param_name and param_name in inputs_used:
                    param_changes.append(ParameterChange(
                        parameter_name=param_name,
                        old_value=inputs_used[param_name],
                        new_value=change.get("new_value"),
                        reason=change.get("reason", "")
                    ))
            
            return RefinementDecision(
                step_id=step_id,
                tool_id=tool_id,
                iteration=iteration,
                quality_score=quality,
                assessment=data.get("assessment", ""),
                action=action,
                confidence=0.8,
                parameter_changes=param_changes,
                reasoning=data.get("reasoning", "")
            )
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Failed to parse, default to accept
            return RefinementDecision(
                step_id=step_id,
                tool_id=tool_id,
                iteration=iteration,
                quality_score=QualityScore.FAIR,
                assessment=f"Could not parse review response: {response_text[:200]}",
                action=RefinementAction.ACCEPT,
                confidence=0.5,
                reasoning=f"Parse error: {str(e)}, defaulting to accept"
            )
    
    def should_refine(self, decision: RefinementDecision, iteration: int) -> bool:
        """
        Determine if refinement should be attempted.
        
        Args:
            decision: The refinement decision
            iteration: Current iteration number
            
        Returns:
            True if refinement should be attempted
        """
        if iteration >= self.max_iterations:
            return False
        
        return decision.action == RefinementAction.ADJUST_PARAMS
