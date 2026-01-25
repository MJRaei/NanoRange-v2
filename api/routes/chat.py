"""
Chat API Routes

Handles chat interactions with the NanoRange analysis agent.
"""

import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from nanorange.agent.orchestrator import NanoRangeOrchestrator
from nanorange.agent.meta_tools import get_current_pipeline_for_frontend, has_current_pipeline
from nanorange.storage.file_store import FileStore

router = APIRouter(prefix="/api/chat", tags=["chat"])

UPLOAD_DIR = "uploads"

# Store orchestrator instances per session
user_orchestrators: dict[str, NanoRangeOrchestrator] = {}

# File store for accessing output files
file_store = FileStore()


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
    pipeline: Optional[dict] = None  # Frontend-compatible pipeline if one was built


def ensure_directories():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_orchestrator(session_id: str) -> NanoRangeOrchestrator:
    """Get or create orchestrator for a session."""
    if session_id not in user_orchestrators:
        user_orchestrators[session_id] = NanoRangeOrchestrator(
            session_id=session_id,
            mode="full"
        )
    return user_orchestrators[session_id]


async def run_agent_chat(
    session_id: str, 
    message: str, 
    image_path: Optional[str] = None
) -> str:
    """
    Run a chat with the NanoRange agent.
    
    Args:
        session_id: Session ID for conversation history
        message: User's message
        image_path: Optional path to an uploaded image
        
    Returns:
        Agent response text
    """
    orchestrator = get_orchestrator(session_id)
    
    if image_path and os.path.exists(image_path):
        response = await orchestrator.chat_with_image(message, image_path)
    else:
        response = await orchestrator.chat(message)
    
    return response


def collect_output_images(session_id: str) -> dict:
    """
    Collect all available output images for a session.
    
    Returns:
        Dictionary of image paths
    """
    images = {}
    
    try:
        orchestrator = user_orchestrators.get(session_id)
        if not orchestrator:
            return images
        
        nano_session_id = orchestrator.get_session_id()
        files = file_store.list_files(nano_session_id)
        
        for file_info in files:
            path = file_info["path"]
            name = file_info["name"]
            ext = file_info["extension"].lower()
            
            if ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
                key = name.rsplit(".", 1)[0]
                images[key] = path
                
    except Exception:
        pass
    
    return images


def get_csv_path(session_id: str) -> Optional[str]:
    """Get the path to any CSV file in the session output."""
    try:
        orchestrator = user_orchestrators.get(session_id)
        if not orchestrator:
            return None
        
        nano_session_id = orchestrator.get_session_id()
        files = file_store.list_files(nano_session_id)
        
        for file_info in files:
            if file_info["extension"].lower() == ".csv":
                return file_info["path"]
                
    except Exception:
        pass
    
    return None


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
    Chat with the NanoRange agent.
    
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
        agent_response = await run_agent_chat(
            session_id=session_id,
            message=message,
            image_path=image_path
        )

        images = collect_output_images(session_id)
        csv_path = get_csv_path(session_id)

        # Get pipeline if one was built by the agent
        pipeline_data = None
        if has_current_pipeline():
            pipeline_data = get_current_pipeline_for_frontend()

        return AnalysisResult(
            success=True,
            message=agent_response,
            images=images,
            csv_path=csv_path,
            session_id=session_id,
            pipeline=pipeline_data
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
