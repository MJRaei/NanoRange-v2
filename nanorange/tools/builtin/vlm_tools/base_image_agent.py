"""
Base class for Gemini image processing agents.

Provides common functionality for Gemini-powered image tools including:
- Client initialization
- Token usage tracking
- Image processing pipeline
"""

from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image
from google import genai
from google.genai import types

from nanorange.settings import GOOGLE_API_KEY


class BaseImageAgent:
    """
    Base class for Gemini image processing agents.
    
    Handles client initialization, image processing, and token tracking.
    Subclasses should override the instruction or provide it at runtime.
    """
    
    def __init__(
        self,
        model: str,
        instruction: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """
        Initialize the base image agent.
        
        Args:
            model: The Gemini model to use for processing
            instruction: Default instruction/prompt for the model
            api_key: API key (defaults to settings)
        """
        self.client = genai.Client(api_key=api_key or GOOGLE_API_KEY)
        self.model = model
        self.default_instruction = instruction or ""
        
        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.processed_count = 0
        self.failed_count = 0
    
    def process_image(
        self,
        input_path: str,
        output_path: str,
        instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single image with Gemini.
        
        Args:
            input_path: Path to the input image
            output_path: Path to save the processed image
            instruction: Custom instruction (uses default if not provided)
            
        Returns:
            Dictionary with processing results
        """
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            return {
                "success": False,
                "error": f"Input file not found: {input_path}",
                "output_path": None,
            }
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use provided instruction or default
        prompt = instruction or self.default_instruction
        if not prompt:
            return {
                "success": False,
                "error": "No instruction provided for image processing",
                "output_path": None,
            }
        
        try:
            # Load image
            image = Image.open(input_file)
            
            # Generate content with image
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, image],
            )
            
            # Update token usage
            self._update_token_usage(response)
            
            # Extract and save output image
            saved = False
            for part in response.parts:
                if part.inline_data:
                    out_image = part.as_image()
                    out_image.save(str(output_file))
                    saved = True
                    break
            
            if not saved:
                self.failed_count += 1
                return {
                    "success": False,
                    "error": "No image returned by the model",
                    "output_path": None,
                    "model_response": response.text if hasattr(response, 'text') else None,
                }
            
            self.processed_count += 1
            return {
                "success": True,
                "output_path": str(output_file),
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }
            
        except Exception as e:
            self.failed_count += 1
            return {
                "success": False,
                "error": str(e),
                "output_path": None,
            }
    
    def _update_token_usage(self, response: types.GenerateContentResponse) -> None:
        """Update token usage statistics from response."""
        if response.usage_metadata:
            self.total_input_tokens += response.usage_metadata.prompt_token_count
            self.total_output_tokens += response.usage_metadata.candidates_token_count
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get token usage statistics."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
        }
    
    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.processed_count = 0
        self.failed_count = 0
