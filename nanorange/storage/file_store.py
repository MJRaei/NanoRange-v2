"""
File Store - Manages image and result files on disk.

Handles:
- Organizing output files by session/pipeline/step
- Generating unique file names
- Tracking file metadata
"""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileStore:
    """
    Manages files (images, results) on the local filesystem.
    
    Files are organized as:
    base_path/
        sessions/
            {session_id}/
                pipelines/
                    {pipeline_id}/
                        {step_id}/
                            output_{name}_{timestamp}.{ext}
        temp/
            {random_id}.{ext}
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file store.
        
        Args:
            base_path: Base directory for file storage (defaults to ./data/files)
        """
        self.base_path = Path(base_path) if base_path else Path("./data/files")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "sessions").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
    
    def get_session_path(self, session_id: str) -> Path:
        """Get the path for a session's files."""
        path = self.base_path / "sessions" / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_pipeline_path(self, session_id: str, pipeline_id: str) -> Path:
        """Get the path for a pipeline's files."""
        path = self.get_session_path(session_id) / "pipelines" / pipeline_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_step_path(
        self,
        session_id: str,
        pipeline_id: str,
        step_id: str
    ) -> Path:
        """Get the path for a step's output files."""
        path = self.get_pipeline_path(session_id, pipeline_id) / step_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def generate_output_path(
        self,
        session_id: str,
        pipeline_id: str,
        step_id: str,
        output_name: str,
        extension: str = "png"
    ) -> Path:
        """
        Generate a unique path for a step output file.
        
        Args:
            session_id: Session ID
            pipeline_id: Pipeline ID
            step_id: Step ID
            output_name: Output name
            extension: File extension
            
        Returns:
            Path for the output file
        """
        step_path = self.get_step_path(session_id, pipeline_id, step_id)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{output_name}_{timestamp}.{extension}"
        return step_path / filename
    
    def save_file(
        self,
        source_path: str,
        session_id: str,
        pipeline_id: str,
        step_id: str,
        output_name: str,
        copy: bool = True
    ) -> str:
        """
        Save a file to the store.
        
        Args:
            source_path: Path to the source file
            session_id: Session ID
            pipeline_id: Pipeline ID
            step_id: Step ID
            output_name: Output name
            copy: Whether to copy (True) or move (False) the file
            
        Returns:
            Path to the stored file
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Generate destination path
        dest = self.generate_output_path(
            session_id, pipeline_id, step_id,
            output_name, source.suffix.lstrip('.')
        )
        
        # Copy or move
        if copy:
            shutil.copy2(source, dest)
        else:
            shutil.move(source, dest)
        
        return str(dest)
    
    def save_temp_file(
        self,
        source_path: str,
        prefix: str = "temp"
    ) -> str:
        """
        Save a file to the temp directory.
        
        Args:
            source_path: Path to source file
            prefix: Filename prefix
            
        Returns:
            Path to temp file
        """
        source = Path(source_path)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}{source.suffix}"
        dest = self.base_path / "temp" / filename
        
        shutil.copy2(source, dest)
        return str(dest)
    
    def save_json(
        self,
        data: Any,
        session_id: str,
        pipeline_id: str,
        step_id: str,
        output_name: str
    ) -> str:
        """
        Save JSON data to a file.
        
        Args:
            data: Data to serialize
            session_id: Session ID
            pipeline_id: Pipeline ID
            step_id: Step ID
            output_name: Output name
            
        Returns:
            Path to the JSON file
        """
        path = self.generate_output_path(
            session_id, pipeline_id, step_id,
            output_name, "json"
        )
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return str(path)
    
    def load_json(self, path: str) -> Any:
        """Load JSON data from a file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def list_files(
        self,
        session_id: str,
        pipeline_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in the store.
        
        Args:
            session_id: Session ID
            pipeline_id: Optional pipeline filter
            step_id: Optional step filter
            
        Returns:
            List of file info dictionaries
        """
        if step_id and pipeline_id:
            search_path = self.get_step_path(session_id, pipeline_id, step_id)
        elif pipeline_id:
            search_path = self.get_pipeline_path(session_id, pipeline_id)
        else:
            search_path = self.get_session_path(session_id)
        
        files = []
        for path in search_path.rglob("*"):
            if path.is_file():
                files.append({
                    "path": str(path),
                    "name": path.name,
                    "extension": path.suffix,
                    "size_bytes": path.stat().st_size,
                    "modified_at": datetime.fromtimestamp(
                        path.stat().st_mtime
                    ).isoformat(),
                })
        
        return sorted(files, key=lambda f: f["modified_at"], reverse=True)
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get information about a file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = p.stat()
        return {
            "path": str(p),
            "name": p.name,
            "extension": p.suffix,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "checksum": self._compute_checksum(p),
        }
    
    def _compute_checksum(self, path: Path, algorithm: str = "md5") -> str:
        """Compute file checksum."""
        hasher = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
            return True
        return False
    
    def cleanup_temp(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temp files.
        
        Args:
            max_age_hours: Delete files older than this
            
        Returns:
            Number of files deleted
        """
        temp_path = self.base_path / "temp"
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        deleted = 0
        
        for path in temp_path.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                deleted += 1
        
        return deleted
    
    def cleanup_session(self, session_id: str) -> bool:
        """Delete all files for a session."""
        session_path = self.get_session_path(session_id)
        if session_path.exists():
            shutil.rmtree(session_path)
            return True
        return False
