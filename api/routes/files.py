"""
File Serving Routes

Handles serving of analysis output files (images, HTML, CSV).
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/files", tags=["files"])

OUTPUT_DIR = "output"
SHAPES_DIR = os.path.join(OUTPUT_DIR, "5_shapes")


class FileInfo(BaseModel):
    """Model for file information."""
    name: str
    path: str
    type: str
    interactive_html: str | None = None


class FilesResponse(BaseModel):
    """Response model for listing files."""
    images: List[FileInfo]
    plots: List[FileInfo]
    csv_files: List[FileInfo]


@router.get("/list")
async def list_output_files():
    """
    List all available output files organized by category.
    
    Returns:
        Organized list of images, plots, and CSV files
        - images: All PNG/JPG files EXCEPT size_distribution (with linked interactive HTML if available)
        - plots: Only size_distribution.png (with linked interactive HTML if available)
        - csv_files: All CSV files for data download
    """
    images = []
    plots = []
    csv_files = []
    
    if not os.path.exists(SHAPES_DIR):
        return FilesResponse(images=images, plots=plots, csv_files=csv_files)
    
    html_files = {}
    for filename in os.listdir(SHAPES_DIR):
        if filename.endswith(".html"):
            base_name = filename.replace(".html", "")
            html_files[base_name] = os.path.join(SHAPES_DIR, filename)
    
    for filename in os.listdir(SHAPES_DIR):
        file_path = os.path.join(SHAPES_DIR, filename)
        
        if filename.endswith(".png") or filename.endswith(".jpg"):
            base_name = filename.replace(".png", "").replace(".jpg", "")
            display_name = base_name.replace("_", " ").title()
            interactive_html = html_files.get(base_name)
            
            file_info = FileInfo(
                name=display_name,
                path=file_path,
                type="image",
                interactive_html=interactive_html
            )
            
            if base_name == "size_distribution":
                plots.append(file_info)
            else:
                images.append(file_info)
                
        elif filename.endswith(".csv"):
            csv_files.append(FileInfo(
                name=filename.replace("_", " ").replace(".csv", "").title(),
                path=file_path,
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
    full_path = filepath
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    if full_path.endswith(".png"):
        media_type = "image/png"
    elif full_path.endswith(".jpg") or full_path.endswith(".jpeg"):
        media_type = "image/jpeg"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(full_path, media_type=media_type)


@router.get("/html/{filepath:path}")
async def get_html(filepath: str):
    """
    Serve an HTML file (interactive plots).
    
    Args:
        filepath: Path to the HTML file
    """
    full_path = filepath
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="HTML file not found")
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    return HTMLResponse(content=content)


@router.get("/csv/{filepath:path}")
async def get_csv(filepath: str):
    """
    Serve a CSV file for download.
    
    Args:
        filepath: Path to the CSV file
    """
    full_path = filepath
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    return FileResponse(
        full_path,
        media_type="text/csv",
        filename=os.path.basename(full_path)
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
    
    full_path = filepath
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    preview_data = []
    with open(full_path, 'r') as f:
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

