"""
Artifact Manager - Saves and organizes outputs from each refinement iteration.

Provides structured storage for:
- Images from each iteration of each step
- Organized by session > pipeline > step > iteration
- Easy retrieval for comparison and debugging

Now uses the same sessions folder structure as normal execution for consistency.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from nanorange import settings


class ArtifactManager:
    """
    Manages artifacts (images, outputs) from refinement iterations.

    Storage structure (now consistent with FileStore):
    {base_path}/
        sessions/
            {session_id}/
                pipelines/
                    {pipeline_id}/
                        {step_id}/
                            iteration_1/
                                output_image.jpg
                                metadata.json
                            iteration_2/
                                output_image.jpg
                                metadata.json
                            final/
                                output_image.jpg
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        base_path: Optional[str] = None
    ):
        """
        Initialize the artifact manager.

        Args:
            session_id: Session identifier (for consistent path with normal execution)
            pipeline_id: Pipeline identifier
            pipeline_name: Human-readable pipeline name
            base_path: Base directory for artifacts (defaults to settings.FILE_STORE_PATH)
        """
        self.base_path = Path(base_path or settings.FILE_STORE_PATH)
        self.session_id = session_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.pipeline_id = pipeline_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.pipeline_name = pipeline_name or "unnamed_pipeline"

        self.pipeline_path = (
            self.base_path / "sessions" / self.session_id / "pipelines" /
            self._sanitize_name(self.pipeline_id)
        )
        self.pipeline_path.mkdir(parents=True, exist_ok=True)

        self._artifacts: Dict[str, Dict[int, Dict[str, str]]] = {}
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as directory/file name."""
        sanitized = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-.")
        return sanitized[:100]
    
    def get_step_path(self, step_name: str) -> Path:
        """Get the directory path for a step."""
        step_path = self.pipeline_path / self._sanitize_name(step_name)
        step_path.mkdir(parents=True, exist_ok=True)
        return step_path
    
    def get_iteration_path(self, step_name: str, iteration: int) -> Path:
        """Get the directory path for a specific iteration."""
        iter_path = self.get_step_path(step_name) / f"iteration_{iteration}"
        iter_path.mkdir(parents=True, exist_ok=True)
        return iter_path
    
    def save_iteration_artifact(
        self,
        step_id: str,
        step_name: str,
        iteration: int,
        artifact_name: str,
        source_path: str,
        artifact_type: str = "image"
    ) -> Optional[str]:
        """
        Save an artifact from an iteration.
        
        Args:
            step_id: Step identifier
            step_name: Human-readable step name
            iteration: Iteration number (1-based)
            artifact_name: Name for the artifact (e.g., "output_image", "mask")
            source_path: Path to the source file to copy
            artifact_type: Type of artifact ("image", "data", "other")
            
        Returns:
            Path to the saved artifact, or None if save failed
        """
        source = Path(source_path)
        if not source.exists():
            return None
        
        iter_path = self.get_iteration_path(step_name, iteration)
        
        suffix = source.suffix or ".png"
        dest_name = f"{self._sanitize_name(artifact_name)}{suffix}"
        dest_path = iter_path / dest_name
        
        try:
            shutil.copy2(source, dest_path)
            
            if step_id not in self._artifacts:
                self._artifacts[step_id] = {}
            if iteration not in self._artifacts[step_id]:
                self._artifacts[step_id][iteration] = {}
            
            self._artifacts[step_id][iteration][artifact_name] = str(dest_path)
            
            return str(dest_path)
            
        except Exception:
            return None
    
    def save_iteration_outputs(
        self,
        step_id: str,
        step_name: str,
        iteration: int,
        outputs: Dict[str, Any],
        image_keys: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Save all image outputs from an iteration.
        
        Args:
            step_id: Step identifier
            step_name: Human-readable step name
            iteration: Iteration number
            outputs: Dictionary of outputs from the step
            image_keys: Optional list of keys that contain image paths.
                       If None, attempts to detect automatically.
            
        Returns:
            Dictionary mapping output names to saved artifact paths
        """
        saved = {}
        
        if image_keys is None:
            image_keys = self._detect_image_outputs(outputs)
        
        for key in image_keys:
            if key in outputs:
                value = outputs[key]
                if isinstance(value, str) and Path(value).exists():
                    saved_path = self.save_iteration_artifact(
                        step_id=step_id,
                        step_name=step_name,
                        iteration=iteration,
                        artifact_name=key,
                        source_path=value,
                        artifact_type="image"
                    )
                    if saved_path:
                        saved[key] = saved_path
        
        return saved
    
    def _detect_image_outputs(self, outputs: Dict[str, Any]) -> List[str]:
        """Detect which outputs are likely image paths."""
        image_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif'}
        image_keys = []
        
        for key, value in outputs.items():
            if isinstance(value, str):
                path = Path(value)
                if path.suffix.lower() in image_extensions:
                    image_keys.append(key)
        
        return image_keys
    
    def save_metadata(
        self,
        step_id: str,
        step_name: str,
        iteration: int,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save metadata for an iteration.
        
        Args:
            step_id: Step identifier
            step_name: Human-readable step name
            iteration: Iteration number
            metadata: Metadata dictionary to save
            
        Returns:
            Path to saved metadata file
        """
        import json
        
        iter_path = self.get_iteration_path(step_name, iteration)
        meta_path = iter_path / "metadata.json"
        
        try:
            serializable = self._make_serializable(metadata)
            
            with open(meta_path, 'w') as f:
                json.dump(serializable, f, indent=2)
            
            return str(meta_path)
            
        except Exception:
            return None
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable form."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'value'):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            try:
                import json
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    def mark_final(
        self,
        step_id: str,
        step_name: str,
        final_iteration: int
    ) -> Optional[str]:
        """
        Mark which iteration was accepted as final and create a link/copy.
        
        Args:
            step_id: Step identifier
            step_name: Human-readable step name
            final_iteration: Which iteration was accepted
            
        Returns:
            Path to the final directory
        """
        step_path = self.get_step_path(step_name)
        final_path = step_path / "final"
        final_path.mkdir(parents=True, exist_ok=True)
        
        if step_id in self._artifacts and final_iteration in self._artifacts[step_id]:
            for artifact_name, artifact_path in self._artifacts[step_id][final_iteration].items():
                source = Path(artifact_path)
                if source.exists():
                    dest = final_path / source.name
                    try:
                        shutil.copy2(source, dest)
                    except Exception:
                        pass
        
        marker_path = final_path / "iteration_info.txt"
        try:
            with open(marker_path, 'w') as f:
                f.write(f"Final iteration: {final_iteration}\n")
                f.write(f"Step: {step_name}\n")
                f.write(f"Step ID: {step_id}\n")
        except Exception:
            pass
        
        return str(final_path)
    
    def get_artifacts_for_step(self, step_id: str) -> Dict[int, Dict[str, str]]:
        """Get all saved artifacts for a step, organized by iteration."""
        return self._artifacts.get(step_id, {})
    
    def get_all_artifacts(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        """Get all saved artifacts, organized by step and iteration."""
        return self._artifacts.copy()
    
    def get_artifact_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all saved artifacts.

        Returns:
            Summary with paths and counts
        """
        summary = {
            "session_id": self.session_id,
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "base_path": str(self.pipeline_path),
            "steps": {}
        }
        
        for step_id, iterations in self._artifacts.items():
            step_summary = {
                "iterations": {},
                "total_iterations": len(iterations)
            }
            
            for iteration, artifacts in iterations.items():
                step_summary["iterations"][iteration] = {
                    "artifact_count": len(artifacts),
                    "artifacts": artifacts
                }
            
            summary["steps"][step_id] = step_summary
        
        return summary
    
    def cleanup_except_final(self, step_id: str, step_name: str) -> None:
        """
        Remove iteration folders except the final one (to save space).
        
        Args:
            step_id: Step identifier
            step_name: Human-readable step name
        """
        step_path = self.get_step_path(step_name)
        
        for item in step_path.iterdir():
            if item.is_dir() and item.name.startswith("iteration_"):
                try:
                    shutil.rmtree(item)
                except Exception:
                    pass
        
        if step_id in self._artifacts:
            self._artifacts[step_id].clear()
