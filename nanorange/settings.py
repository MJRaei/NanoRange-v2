"""
NanoRange settings and configuration.

Centralizes all configuration values including API keys and model settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Model Configuration
DEFAULT_LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
IMAGE_MODEL_COLORIZER = os.getenv("GEMINI_IMAGE_MODEL_COLORIZER", "gemini-3-pro-image-preview")

# Image Reviewer Model - for iterative refinement feedback
IMAGE_REVIEWER_MODEL = os.getenv("IMAGE_REVIEWER_MODEL", "gemini-2.5-flash-image")

# Storage Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/nanorange.db")
FILE_STORE_PATH = os.getenv("FILE_STORE_PATH", "./data/files")

# Processing Configuration
DEFAULT_TILE_SIZE = int(os.getenv("DEFAULT_TILE_SIZE", "512"))
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "4096"))

# Iterative Refinement Configuration
MAX_TOOL_ITERATIONS = int(os.getenv("MAX_TOOL_ITERATIONS", "3"))
REFINEMENT_ENABLED = os.getenv("REFINEMENT_ENABLED", "true").lower() == "true"
