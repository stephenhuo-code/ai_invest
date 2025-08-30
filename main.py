#!/usr/bin/env python3
"""
AI Invest Trend API - Main Entry Point

This is the main entry point that imports and runs the FastAPI application
from the new layered architecture.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the simplified FastAPI app from the presentation layer
from src.presentation.api.main_simplified import app

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )