"""
File Serving Routes

Handles serving of analysis output files (images, HTML, CSV).
"""

import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from nanorange.storage.file_store import FileStore

router = APIRouter(prefix="/api/files", tags=["files"])

file_store = FileStore()


class FileInfo(BaseModel):
    """Model for file information."""
    name: str
    path: str
    type: str
    interactive_html: Optional[str] = None


class FilesResponse(BaseModel):
    """Response model for listing files."""
    images: List[FileInfo]
    plots: List[FileInfo]
    csv_files: List[FileInfo]


@router.get("/list")
async def list_output_files(session_id: Optional[str] = Query(None)):
    """
    List all available output files organized by category.
    
    Args:
        session_id: Optional session ID to filter files
    
    Returns:
        Organized list of images, plots, and CSV files
    """
    images = []
    plots = []
    csv_files = []
    
    if not session_id:
        return FilesResponse(images=images, plots=plots, csv_files=csv_files)
    
    try:
        files = file_store.list_files(session_id)
    except Exception:
        return FilesResponse(images=images, plots=plots, csv_files=csv_files)
    
    html_files = {}
    for file_info in files:
        if file_info["extension"].lower() == ".html":
            base_name = file_info["name"].rsplit(".", 1)[0]
            html_files[base_name] = file_info["path"]
    
    for file_info in files:
        ext = file_info["extension"].lower()
        name = file_info["name"]
        path = file_info["path"]
        
        if ext in [".png", ".jpg", ".jpeg"]:
            base_name = name.rsplit(".", 1)[0]
            display_name = base_name.replace("_", " ").title()
            interactive_html = html_files.get(base_name)
            
            info = FileInfo(
                name=display_name,
                path=path,
                type="image",
                interactive_html=interactive_html
            )
            
            if any(x in base_name.lower() for x in ["distribution", "histogram", "chart", "plot"]):
                plots.append(info)
            else:
                images.append(info)
                
        elif ext == ".csv":
            csv_files.append(FileInfo(
                name=name.replace("_", " ").replace(".csv", "").title(),
                path=path,
                type="csv"
            ))
    
    return FilesResponse(
        images=sorted(images, key=lambda x: x.name),
        plots=sorted(plots, key=lambda x: x.name),
        csv_files=sorted(csv_files, key=lambda x: x.name)
    )


@router.get("/image/{filepath:path}")
async def get_image(filepath: str):
    """
    Serve an image file.
    
    Args:
        filepath: Path to the image file
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    if filepath.endswith(".png"):
        media_type = "image/png"
    elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filepath.endswith(".tif") or filepath.endswith(".tiff"):
        media_type = "image/tiff"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(filepath, media_type=media_type)


@router.get("/html/{filepath:path}")
async def get_html(filepath: str):
    """
    Serve an HTML file (interactive plots).
    
    Args:
        filepath: Path to the HTML file
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="HTML file not found")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    return HTMLResponse(content=content)


@router.get("/csv/{filepath:path}")
async def get_csv(filepath: str):
    """
    Serve a CSV file for download.
    
    Args:
        filepath: Path to the CSV file
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    return FileResponse(
        filepath,
        media_type="text/csv",
        filename=os.path.basename(filepath)
    )


@router.get("/csv-preview/{filepath:path}")
async def preview_csv(filepath: str, rows: int = 10):
    """
    Preview first N rows of a CSV file.
    
    Args:
        filepath: Path to the CSV file
        rows: Number of rows to preview
    """
    import csv
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    preview_data = []
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i >= rows:
                break
            preview_data.append(row)
    
    return {
        "headers": preview_data[0] if preview_data else [],
        "data": preview_data[1:] if len(preview_data) > 1 else [],
        "total_preview_rows": len(preview_data) - 1
    }
