"""
FastAPI Backend

Main API server for Nashville Numbers Converter.
Provides endpoint for converting chord chart PDFs.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.pdf_processor import (
    PDFProcessor,
    PDFProcessingError,
    get_supported_keys,
    get_processing_stats
)


# Initialize FastAPI app
app = FastAPI(
    title="Nashville Numbers Converter",
    description="Convert chord chart PDFs to Nashville Number System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PDF processor
pdf_processor = PDFProcessor()

# Temporary file storage directory
TEMP_DIR = Path("/tmp/nashville_converter")

# File size limit (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def ensure_temp_dir():
    """
    Ensure temp directory exists (lazy initialization).

    This is called on-demand rather than at module load time to avoid
    filesystem errors during serverless cold starts.
    """
    TEMP_DIR.mkdir(exist_ok=True)


# Pydantic models for API responses
class ConversionResponse(BaseModel):
    """Response model for successful conversion."""
    success: bool
    message: str
    download_url: str
    stats: dict


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool
    error: str
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    capabilities: dict


# Background task for cleaning up old temp files
async def cleanup_temp_file(file_path: str, delay_minutes: int = 15):
    """
    Delete a temporary file after a delay.

    Args:
        file_path: Path to file to delete
        delay_minutes: Minutes to wait before deletion
    """
    await asyncio.sleep(delay_minutes * 60)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # Ignore cleanup errors


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded PDF file.

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )

    # Check MIME type
    if file.content_type not in ['application/pdf', 'application/x-pdf']:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. File must be a PDF."
        )


@app.get("/", response_model=HealthResponse)
async def root():
    """
    Health check endpoint.

    Returns:
        Health status and capabilities
    """
    capabilities = get_processing_stats()
    return {
        "status": "healthy",
        "capabilities": capabilities
    }


@app.get("/keys")
async def get_keys():
    """
    Get list of supported musical keys.

    Returns:
        List of supported keys
    """
    return {
        "keys": get_supported_keys()
    }


@app.post("/convert")
async def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    key: str = Form(...),
    mode: str = Form("major")
):
    """
    Convert a chord chart PDF to Nashville Number System.

    Args:
        file: Uploaded PDF file
        key: Musical key (e.g., "C", "G", "Bb")
        mode: "major" or "minor"

    Returns:
        FileResponse with converted PDF or error details
    """
    # Validate file
    validate_pdf_file(file)

    # Validate key
    supported_keys = get_supported_keys()
    if key not in supported_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key: {key}. Supported keys: {', '.join(supported_keys)}"
        )

    # Validate mode
    if mode not in ["major", "minor"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {mode}. Must be 'major' or 'minor'."
        )

    # Ensure temp directory exists (lazy initialization for serverless)
    ensure_temp_dir()

    # Generate unique IDs for temp files
    file_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"input_{file_id}.pdf"
    output_path = TEMP_DIR / f"output_{file_id}.pdf"

    try:
        # Read and validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f} MB."
            )

        # Save uploaded file
        with open(input_path, "wb") as f:
            f.write(contents)

        # Process the PDF
        try:
            result = pdf_processor.process_pdf(
                str(input_path),
                str(output_path),
                key=key,
                mode=mode
            )
        except PDFProcessingError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Schedule cleanup of input file
        background_tasks.add_task(cleanup_temp_file, str(input_path), delay_minutes=1)

        # Schedule cleanup of output file after 15 minutes
        background_tasks.add_task(cleanup_temp_file, str(output_path), delay_minutes=15)

        # Return the converted PDF
        return FileResponse(
            path=str(output_path),
            media_type="application/pdf",
            filename=f"nashville_{file.filename}",
            headers={
                "X-Conversion-Stats": str(result.get('total_chords_converted', 0)),
                "X-Processing-Method": result.get('processing_method', 'unknown')
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        # Clean up files
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        raise

    except Exception as e:
        # Clean up files
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/validate")
async def validate_pdf_endpoint(
    file: UploadFile = File(...)
):
    """
    Validate a PDF and check if it can be processed.

    Args:
        file: Uploaded PDF file

    Returns:
        Validation results
    """
    # Validate file
    validate_pdf_file(file)

    # Ensure temp directory exists (lazy initialization for serverless)
    ensure_temp_dir()

    # Generate unique ID for temp file
    file_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"validate_{file_id}.pdf"

    try:
        # Save uploaded file temporarily
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f} MB."
            )

        with open(input_path, "wb") as f:
            f.write(contents)

        # Validate the PDF
        validation_result = pdf_processor.validate_pdf(str(input_path))

        # Clean up
        input_path.unlink()

        return validation_result

    except Exception as e:
        # Clean up
        if input_path.exists():
            input_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


# Periodic cleanup task to remove old temp files
# Note: Disabled for serverless compatibility. In serverless environments,
# lifecycle events are not supported when using Mangum with lifespan="off".
# Cleanup is handled by background tasks for files created during each request.
# @app.on_event("startup")
# async def startup_event():
#     """
#     Run cleanup on startup.
#     """
#     # Clean up any leftover temp files from previous runs
#     for file_path in TEMP_DIR.glob("*.pdf"):
#         try:
#             # Check file age
#             file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
#             if file_age > timedelta(minutes=30):
#                 file_path.unlink()
#         except Exception:
#             pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
