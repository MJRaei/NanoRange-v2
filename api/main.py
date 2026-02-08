"""
NanoRange API Server

Main FastAPI application for the NanoRange cryo-TEM analysis tool.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import chat_router, files_router
from api.routes.pipeline import router as pipeline_router
from nanorange.core.registry import get_registry

app = FastAPI(
    title="NanoRange API",
    description="API for Gemini-powered nanoparticle analysis from cryo-TEM images",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data/files"
UPLOADS_DIR = "uploads"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/static/data", StaticFiles(directory=DATA_DIR), name="data")
app.mount("/static/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(chat_router)
app.include_router(files_router)
app.include_router(pipeline_router)


@app.on_event("startup")
async def startup_event():
    """Initialize backend components on startup."""
    registry = get_registry()
    num_tools = registry.discover_tools("nanorange.tools.builtin")
    print(f"✓ Loaded {len(registry.list_tools())} tools ({num_tools} discovered)")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NanoRange API",
        "version": "0.1.0",
        "description": "Gemini-powered nanoparticle analysis from cryo-TEM images",
        "docs": "/docs",
        "health": "/api/chat/health"
    }

