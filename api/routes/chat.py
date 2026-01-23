"""
Chat API Routes

Handles chat interactions with the cryo-TEM analysis agent.
"""

import os
import sys
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from nanorange.agent import root_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

session_service = InMemorySessionService()

user_sessions = {}


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    image_path: Optional[str] = None


class AnalysisResult(BaseModel):
    """Model for analysis results returned to the frontend."""
    success: bool
    message: str
    images: dict = {}
    csv_path: Optional[str] = None
    session_id: str


def ensure_directories():
    """Ensure upload and output directories exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


async def run_agent_chat(session_id: str, message: str, image_path: Optional[str] = None) -> tuple[str, bool]:
    """
    Run a chat with the ADK agent.
    
    Args:
        session_id: Session ID for conversation history
        message: User's message
        image_path: Optional path to an uploaded image
        
    Returns:
        Tuple of (agent response, whether analysis was run)
    """
    if image_path and os.path.exists(image_path):
        full_message = f"{message}\n\n[User has uploaded an image at: {image_path}]"
    else:
        full_message = message
    
    if session_id not in user_sessions:
        session = await session_service.create_session(
            app_name="nanorange",
            user_id=session_id,
        )
        user_sessions[session_id] = session.id
    
    adk_session_id = user_sessions[session_id]
    
    runner = Runner(
        agent=root_agent,
        app_name="nanorange",
        session_service=session_service,
    )
    
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=full_message)]
    )
    
    shapes_dir = "output/5_shapes"
    csv_path = os.path.join(shapes_dir, "detected_shapes.csv")
    pre_run_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0
    
    response_text = ""
    
    async for event in runner.run_async(
        user_id=session_id,
        session_id=adk_session_id,
        new_message=content,
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    
    post_run_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0
    analysis_run = post_run_mtime > pre_run_mtime
    
    return response_text, analysis_run


def collect_output_images() -> dict:
    """
    Collect all available output images after analysis.
    
    Returns:
        Dictionary of image paths
    """
    images = {}
    shapes_dir = "output/5_shapes"
    
    if not os.path.exists(shapes_dir):
        return images
    
    if os.path.exists(os.path.join(shapes_dir, "thresholded_with_shapes.png")):
        images["thresholded_with_shapes"] = f"{shapes_dir}/thresholded_with_shapes.png"
    
    if os.path.exists(os.path.join(shapes_dir, "size_distribution.png")):
        images["size_distribution"] = f"{shapes_dir}/size_distribution.png"
    
    if os.path.exists(os.path.join(shapes_dir, "original.png")):
        images["original"] = f"{shapes_dir}/original.png"
    
    if os.path.exists(os.path.join(shapes_dir, "final_colorized.png")):
        images["colorized"] = f"{shapes_dir}/final_colorized.png"
    
    if os.path.exists(os.path.join(shapes_dir, "final_thresholded.png")):
        images["thresholded"] = f"{shapes_dir}/final_thresholded.png"
    
    if os.path.exists(os.path.join(shapes_dir, "original_with_shapes.png")):
        images["original_with_shapes"] = f"{shapes_dir}/original_with_shapes.png"
    
    if os.path.exists(os.path.join(shapes_dir, "colorized_with_shapes.png")):
        images["colorized_with_shapes"] = f"{shapes_dir}/colorized_with_shapes.png"
    
    html_files = [
        "original_with_shapes.html",
        "colorized_with_shapes.html",
        "thresholded_with_shapes.html",
        "size_distribution.html"
    ]
    
    for html_file in html_files:
        if os.path.exists(os.path.join(shapes_dir, html_file)):
            key = html_file.replace(".html", "_html")
            images[key] = f"{shapes_dir}/{html_file}"
    
    return images


def get_csv_path() -> Optional[str]:
    """Get the path to the CSV file if it exists."""
    csv_path = "output/5_shapes/detected_shapes.csv"
    return csv_path if os.path.exists(csv_path) else None


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image for analysis.
    
    Returns the path to the uploaded image.
    """
    ensure_directories()
    
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/tiff"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "success": True,
        "file_path": file_path,
        "filename": file.filename
    }


@router.post("/analyze")
async def analyze_endpoint(
    message: str = Form(...),
    image_path: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Chat with the NanOrange agent.
    
    The agent decides what to do based on the user's message
    and whether an image has been provided.
    
    Args:
        message: User's message/instructions
        image_path: Optional path to an uploaded image
        session_id: Optional session ID for conversation continuity
        
    Returns:
        Agent's response, potentially with analysis results
    """
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    
    try:
        agent_response, analysis_run = await run_agent_chat(
            session_id=session_id,
            message=message,
            image_path=image_path
        )
        
        images = collect_output_images() if analysis_run else {}
        csv_path = get_csv_path() if analysis_run else None
        
        return AnalysisResult(
            success=True,
            message=agent_response,
            images=images,
            csv_path=csv_path,
            session_id=session_id
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return AnalysisResult(
            success=False,
            message=f"An error occurred: {str(e)}",
            session_id=session_id
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nanorange-api"}
