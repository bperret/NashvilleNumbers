"""
FastAPI Application for Nashville Numbers Converter

Clean, minimal API with proper error handling.
"""

import uuid
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError

from backend.app import config
from backend.app.models import ConversionRequest, ConversionMode
from backend.app.config import CORS_ORIGINS, TEMP_DIR, TEMP_FILE_TTL_MINUTES
from backend.pipeline.processor import NashvillePipeline
from backend.utils.cleanup import TempFileManager
from backend.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Ensure temp directory exists
config.ensure_temp_dir()

# Initialize FastAPI app
app = FastAPI(
    title="Nashville Numbers Converter",
    description="Convert chord chart PDFs to Nashville Number System",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize temp file manager
temp_manager = TempFileManager(TEMP_DIR, TEMP_FILE_TTL_MINUTES)

# Initialize pipeline
pipeline = NashvillePipeline(temp_manager)


# Response models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    capabilities: dict


class KeysResponse(BaseModel):
    """Supported keys response"""
    keys: list


# Background task for cleanup
async def cleanup_output_file(file_path: Path, delay_minutes: int = 15):
    """Delete output file after delay"""
    import asyncio
    await asyncio.sleep(delay_minutes * 60)
    temp_manager.cleanup_file(file_path)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status and capabilities.
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "capabilities": {
            "text_pdf_support": True,
            "ocr_support": False,
            "supported_keys": config.SUPPORTED_KEYS,
            "supported_modes": ["major", "minor"],
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        }
    }


@app.get("/keys", response_model=KeysResponse)
async def get_supported_keys():
    """
    Get list of supported musical keys.

    Returns:
        List of valid key names
    """
    return {"keys": config.SUPPORTED_KEYS}


@app.post("/convert")
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    key: str = Form(...),
    mode: str = Form("major"),
):
    """
    Convert a chord chart PDF to Nashville Number System.

    Args:
        file: PDF file upload
        key: Musical key (e.g., "C", "G", "Bb")
        mode: "major" or "minor"

    Returns:
        Converted PDF file

    Raises:
        HTTPException: On validation or processing errors
    """
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    logger.set_correlation_id(correlation_id)

    logger.info("Received conversion request", key=key, mode=mode, filename=file.filename)

    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )

    if file.content_type not in ['application/pdf', 'application/x-pdf']:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. File must be a PDF."
        )

    # Validate key
    if key not in config.SUPPORTED_KEYS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key: {key}. Supported keys: {', '.join(config.SUPPORTED_KEYS)}"
        )

    # Validate mode
    if mode not in ["major", "minor"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode}. Must be 'major' or 'minor'."
        )

    try:
        # Read file bytes
        pdf_bytes = await file.read()

        # Create conversion request
        conversion_request = ConversionRequest(
            correlation_id=correlation_id,
            key=key,
            mode=ConversionMode(mode),
        )

        # Process through pipeline
        result, output_path = pipeline.process(pdf_bytes, conversion_request)

        # Check for errors
        if not result.success or not output_path:
            error_message = result.error.message if result.error else "Unknown error"
            logger.error("Conversion failed", error=error_message)

            raise HTTPException(
                status_code=400,
                detail=error_message
            )

        # Schedule cleanup of output file
        background_tasks.add_task(cleanup_output_file, output_path, delay_minutes=15)

        # Return converted PDF
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"nashville_{file.filename}",
            headers={
                "X-Correlation-ID": correlation_id,
                "X-Chords-Converted": str(result.total_chords_converted),
                "X-Processing-Time": f"{result.processing_time_seconds:.2f}",
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error in conversion", exception=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# Startup event - cleanup old files
@app.on_event("startup")
async def startup_event():
    """Run cleanup on startup"""
    logger.info("Nashville Numbers Converter starting up")
    temp_manager.cleanup_old_files()


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
