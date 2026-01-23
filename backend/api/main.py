"""
FastAPI Backend

Main API server for Nashville Numbers Converter.
Provides endpoint for converting chord chart PDFs.
"""

import os
import uuid
import asyncio
import traceback
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, APIRouter
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.pdf_processor import (
    PDFProcessor,
    PDFProcessingError,
    get_supported_keys,
    get_processing_stats
)


# Generate a trace ID for request tracking
def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking."""
    return f"trace-{uuid.uuid4().hex[:12]}"


def run_component_diagnostic(name: str, test_func) -> Dict[str, Any]:
    """
    Run a diagnostic test on a component and capture results.

    Args:
        name: Component name
        test_func: Function to test the component

    Returns:
        Diagnostic result dictionary
    """
    start_time = datetime.now()
    try:
        result = test_func()
        return {
            "name": name,
            "status": "ok",
            "message": result if isinstance(result, str) else "Component loaded successfully",
            "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
        }


def run_all_diagnostics() -> Dict[str, Any]:
    """
    Run diagnostics on all components and return comprehensive results.

    Returns:
        Dictionary with all diagnostic results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "components": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0
        }
    }

    # Test 1: pdfplumber (PDF text extraction)
    def test_pdfplumber():
        import pdfplumber
        return f"pdfplumber v{pdfplumber.__version__} loaded"
    results["components"].append(run_component_diagnostic("pdfplumber", test_pdfplumber))

    # Test 2: reportlab (PDF generation)
    def test_reportlab():
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        return "reportlab canvas module loaded"
    results["components"].append(run_component_diagnostic("reportlab", test_reportlab))

    # Test 3: PyPDF2 (PDF merging)
    def test_pypdf2():
        from PyPDF2 import PdfReader, PdfWriter
        return "PyPDF2 reader/writer loaded"
    results["components"].append(run_component_diagnostic("PyPDF2", test_pypdf2))

    # Test 4: Pillow (image processing)
    def test_pillow():
        from PIL import Image
        return f"Pillow (PIL) loaded"
    results["components"].append(run_component_diagnostic("Pillow", test_pillow))

    # Test 5: Temp directory access
    def test_temp_dir():
        test_path = TEMP_DIR / f"test_{uuid.uuid4().hex[:8]}.txt"
        TEMP_DIR.mkdir(exist_ok=True)
        test_path.write_text("test")
        test_path.unlink()
        return f"Temp directory writable: {TEMP_DIR}"
    results["components"].append(run_component_diagnostic("temp_directory", test_temp_dir))

    # Test 6: Chord parser
    def test_chord_parser():
        from backend.core.chord_parser import parse_chord, is_likely_chord
        test_chord = parse_chord("Cmaj7")
        if test_chord is None:
            raise ValueError("Failed to parse test chord 'Cmaj7'")
        return f"Chord parser working: parsed 'Cmaj7' -> root={test_chord.root}"
    results["components"].append(run_component_diagnostic("chord_parser", test_chord_parser))

    # Test 7: Nashville converter
    def test_nashville_converter():
        from backend.core.nashville_converter import convert_chord_to_nashville
        from backend.core.chord_parser import parse_chord
        chord = parse_chord("G")
        nashville = convert_chord_to_nashville(chord, "C", "major")
        if nashville != "5":
            raise ValueError(f"Unexpected result: G in C major should be 5, got {nashville}")
        return f"Nashville converter working: G -> 5 (in C major)"
    results["components"].append(run_component_diagnostic("nashville_converter", test_nashville_converter))

    # Test 8: Text PDF handler imports
    def test_text_pdf_handler():
        from backend.core.text_pdf_handler import extract_chords_from_text_pdf, detect_if_text_pdf
        return "Text PDF handler functions loaded"
    results["components"].append(run_component_diagnostic("text_pdf_handler", test_text_pdf_handler))

    # Test 9: PDF renderer imports
    def test_pdf_renderer():
        from backend.core.pdf_renderer import render_text_pdf_with_nashville
        return "PDF renderer functions loaded"
    results["components"].append(run_component_diagnostic("pdf_renderer", test_pdf_renderer))

    # Calculate summary
    results["summary"]["total"] = len(results["components"])
    results["summary"]["passed"] = sum(1 for c in results["components"] if c["status"] == "ok")
    results["summary"]["failed"] = sum(1 for c in results["components"] if c["status"] == "error")
    results["all_ok"] = results["summary"]["failed"] == 0

    return results


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


# Global exception handler to catch any unhandled exceptions
# This prevents FUNCTION_INVOCATION_FAILED errors in serverless environments
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch any unhandled exceptions and return a proper JSON response.
    This prevents serverless function crashes from unhandled errors.
    """
    trace_id = generate_trace_id()

    # Get error details safely
    try:
        error_msg = str(exc)
    except Exception:
        error_msg = "Unknown error occurred"

    try:
        error_type = type(exc).__name__
    except Exception:
        error_type = "UnknownError"

    try:
        error_traceback = traceback.format_exc()
    except Exception:
        error_traceback = "Traceback unavailable"

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "trace_id": trace_id,
            "suggestion": "Run GET /diagnostics to check component status",
            "traceback": error_traceback
        }
    )


# Simple ping endpoint for health checks (no dependencies)
@app.get("/ping")
@app.get("/api/ping")
async def ping():
    """Simple health check that requires no heavy dependencies."""
    return {
        "status": "ok",
        "message": "Nashville Numbers Converter API is running",
        "python_version": sys.version.split()[0]
    }

# Create API router for all endpoints
# This allows mounting at both "/" and "/api" for compatibility
api_router = APIRouter()

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
    # Check if file exists
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="No file provided. Please upload a PDF file."
        )

    # Check filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File has no filename. Please upload a valid PDF file."
        )

    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are accepted."
        )

    # Check MIME type (be more lenient - some browsers send different types)
    valid_content_types = [
        'application/pdf',
        'application/x-pdf',
        'application/octet-stream',  # Some browsers send this for any binary
        None,  # Sometimes content_type is not set
    ]
    if file.content_type not in valid_content_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type. File must be a PDF."
        )


@api_router.get("/", response_model=HealthResponse)
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


@api_router.get("/keys")
async def get_keys():
    """
    Get list of supported musical keys.

    Returns:
        List of supported keys
    """
    return {
        "keys": get_supported_keys()
    }


@api_router.get("/diagnostics")
async def get_diagnostics():
    """
    Run comprehensive diagnostics on all components.

    This endpoint tests each component individually to help identify
    issues in serverless environments. Use this when you see generic
    "server error" messages to identify which component is failing.

    Returns:
        Detailed diagnostic results for all components
    """
    trace_id = generate_trace_id()
    try:
        results = run_all_diagnostics()
        results["trace_id"] = trace_id
        return results
    except Exception as e:
        return {
            "trace_id": trace_id,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }


@api_router.post("/convert")
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
    # Generate trace ID for this request
    trace_id = generate_trace_id()
    current_step = "initialization"

    # Validate file
    try:
        current_step = "file_validation"
        validate_pdf_file(file)
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.detail,
                "trace_id": trace_id,
                "step": current_step
            }
        )

    # Validate key
    current_step = "key_validation"
    supported_keys = get_supported_keys()
    if key not in supported_keys:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid key: {key}. Supported keys: {', '.join(supported_keys)}",
                "trace_id": trace_id,
                "step": current_step
            }
        )

    # Validate mode
    current_step = "mode_validation"
    if mode not in ["major", "minor"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid mode: {mode}. Must be 'major' or 'minor'.",
                "trace_id": trace_id,
                "step": current_step
            }
        )

    # Ensure temp directory exists (lazy initialization for serverless)
    current_step = "temp_directory_setup"
    try:
        ensure_temp_dir()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to create temp directory: {str(e)}",
                "trace_id": trace_id,
                "step": current_step,
                "suggestion": "This may be a serverless environment issue. Try running /diagnostics to check component status."
            }
        )

    # Generate unique IDs for temp files
    file_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"input_{file_id}.pdf"
    output_path = TEMP_DIR / f"output_{file_id}.pdf"

    try:
        # Read and validate file size
        current_step = "file_upload"
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f} MB.",
                    "trace_id": trace_id,
                    "step": current_step,
                    "file_size_bytes": len(contents)
                }
            )

        # Save uploaded file
        current_step = "file_save"
        with open(input_path, "wb") as f:
            f.write(contents)

        # Process the PDF
        current_step = "pdf_processing"
        try:
            result = pdf_processor.process_pdf(
                str(input_path),
                str(output_path),
                key=key,
                mode=mode
            )
        except PDFProcessingError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": str(e),
                    "trace_id": trace_id,
                    "step": current_step,
                    "processing_error": True
                }
            )

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
                "X-Processing-Method": result.get('processing_method', 'unknown'),
                "X-Trace-ID": trace_id
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        # Clean up files safely
        try:
            if input_path.exists():
                input_path.unlink()
        except Exception:
            pass
        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass
        raise

    except Exception as e:
        # Clean up files safely
        try:
            if input_path.exists():
                input_path.unlink()
        except Exception:
            pass
        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass

        # Get error message safely
        try:
            error_msg = str(e)
        except Exception:
            error_msg = "Unknown error occurred"

        # Get error type safely
        try:
            error_type = type(e).__name__
        except Exception:
            error_type = "UnknownError"

        # Get traceback safely
        try:
            error_traceback = traceback.format_exc()
        except Exception:
            error_traceback = "Traceback unavailable"

        # Enhanced error response with diagnostics context
        error_detail = {
            "error": error_msg,
            "error_type": error_type,
            "trace_id": trace_id,
            "step": current_step,
            "suggestion": "Run GET /diagnostics to check component status",
            "traceback": error_traceback
        }

        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@api_router.post("/validate")
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


# Mount the API router at both "/" and "/api" for compatibility
# - "/" is used for local development (localhost:8000/convert)
# - "/api" is used for Vercel deployment (domain.com/api/convert)
app.include_router(api_router)
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
