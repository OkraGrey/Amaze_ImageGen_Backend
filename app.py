"""
Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from backend.endpoints.generation import router as generation_router
from backend.config.logging_config import setup_logging
from backend.middleware.logging_middleware import LoggingMiddleware
from backend.utils.logger import app_logger
# from backend.routes.generation_routes import router as generation_router
from backend.config.settings import UPLOAD_DIR, RESULT_DIR

# Setup logging first
setup_logging()

# Create FastAPI app
app = FastAPI(title="Image Generation API")

# Add logging middleware (should be added early)
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log application startup
app_logger.info("Image Generation API starting up...")

app.include_router(router=generation_router)
# Include routers - removing the /api prefix since main.py already mounts this app at /api
# app.include_router(generation_router, tags=["generation"])

# Mount static directories
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=RESULT_DIR), name="results")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    app_logger.info("Root endpoint accessed")
    return {"message": "Image Generation API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
