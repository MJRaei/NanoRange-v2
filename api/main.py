"""
NanOrange API Server

Main FastAPI application for the NanOrange cryo-TEM analysis tool.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import chat_router, files_router

app = FastAPI(
    title="NanOrange API",
    description="API for AI-powered nanoparticle analysis from cryo-TEM images",
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NanOrange API",
        "version": "0.1.0",
        "description": "AI-powered nanoparticle analysis from cryo-TEM images",
        "docs": "/docs",
        "health": "/api/chat/health"
    }

