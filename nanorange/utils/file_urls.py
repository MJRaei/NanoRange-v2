"""
Utility functions for generating accessible URLs for files.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import quote


def get_file_url(file_path: str, base_url: str = "/api/files/serve") -> str:
    """
    Convert a file path to an accessible URL.
    
    Args:
        file_path: Absolute or relative file path
        base_url: Base URL for the file serving endpoint
        
    Returns:
        URL to access the file
    """
    path = Path(file_path)
    
    if str(path).startswith("data/files"):
        return f"{base_url}?path={quote(str(path.resolve()))}"
    
    return f"{base_url}?path={quote(str(path.resolve()))}"


def format_file_path_for_agent(file_path: str, include_url: bool = True) -> str:
    """
    Format a file path for display in agent responses.
    
    Args:
        file_path: File path
        include_url: Whether to include an accessible URL
    
    Returns:
        Formatted string with path and optionally URL
    """
    path = Path(file_path)
    
    try:
        repo_root = Path.cwd()
        if path.is_absolute() and path.is_relative_to(repo_root):
            relative_path = path.relative_to(repo_root)
        else:
            relative_path = path
    except (ValueError, AttributeError):
        relative_path = path
    
    if include_url:
        url = get_file_url(file_path)
        return f"{relative_path}\nAccessible at: {url}"
    else:
        return str(relative_path)


def is_file_in_repo(file_path: str, repo_root: Optional[str] = None) -> bool:
    """
    Check if a file is within the repository directory structure.
    
    Args:
        file_path: File path to check
        repo_root: Repository root path (defaults to current working directory)
        
    Returns:
        True if file is in repo structure
    """
    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)
    
    file_path_obj = Path(file_path).resolve()
    repo_root_obj = repo_root.resolve()
    
    try:
        return file_path_obj.is_relative_to(repo_root_obj)
    except AttributeError:
        return str(file_path_obj).startswith(str(repo_root_obj))
