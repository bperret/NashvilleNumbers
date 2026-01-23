"""
Vercel Serverless Function Handler for Nashville Numbers Converter

This module serves as the entry point for the Vercel serverless function.
Vercel's Python runtime has native ASGI support, so we can directly
export the FastAPI app without needing an adapter like Mangum.
"""

import sys
import os
from pathlib import Path

# Ensure backend module can be imported by adding project root to Python path
# In Vercel's serverless environment, we need to explicitly set the path
project_root = Path(__file__).resolve().parent.parent
cwd = Path.cwd()

# Add multiple potential paths for Vercel's environment
paths_to_add = [
    project_root,
    cwd,
    Path("/var/task"),  # Common Vercel/Lambda path
]

for path in paths_to_add:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# Store import error for debugging if it occurs
_import_error = None
_import_traceback = None

def _create_fallback_app(import_error: str, import_traceback: str):
    """
    Create a fallback FastAPI app that reports import errors.
    This ensures we always return valid JSON responses even when the main app fails.
    """
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    fallback = FastAPI(title="Nashville Numbers Converter - Error Mode")

    fallback.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler to ensure JSON responses even for unexpected errors
    @fallback.exception_handler(Exception)
    async def fallback_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": f"Unexpected error in fallback app: {str(exc)}",
                "import_error": import_error,
            }
        )

    @fallback.get("/")
    @fallback.get("/api/")
    async def error_root():
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Failed to import main application",
                "import_error": import_error,
                "traceback": import_traceback,
                "sys_path": sys.path[:10],
                "cwd": str(cwd),
                "project_root": str(project_root),
            }
        )

    @fallback.get("/ping")
    @fallback.get("/api/ping")
    async def error_ping():
        """Simple ping that works even in error mode."""
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Application in error mode - import failed",
                "import_error": import_error,
            }
        )

    @fallback.get("/diagnostics")
    @fallback.get("/api/diagnostics")
    async def error_diagnostics():
        """Diagnostics endpoint that reports the import failure."""
        # Return a diagnostic-like structure so the frontend can display it properly
        return JSONResponse(
            status_code=200,  # Return 200 so frontend processes the response
            content={
                "status": "error",
                "error": "Main application failed to import",
                "import_error": import_error,
                "traceback": import_traceback,
                "python_version": sys.version,
                "sys_path": sys.path[:10],
                "env_vars": {
                    k: v for k, v in os.environ.items()
                    if k.startswith(("PYTHON", "PATH", "VERCEL", "AWS"))
                },
                # Provide diagnostic-like structure for frontend compatibility
                "timestamp": None,
                "components": [
                    {
                        "name": "Application Import",
                        "status": "error",
                        "message": import_error,
                        "duration_ms": 0
                    }
                ],
                "summary": {
                    "total": 1,
                    "passed": 0,
                    "failed": 1
                },
                "all_ok": False
            }
        )

    @fallback.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Main application failed to import",
                "requested_path": path,
                "import_error": import_error,
            }
        )

    return fallback


try:
    # Import and directly export the FastAPI app
    # Vercel's Python runtime will automatically handle ASGI apps
    from backend.api.main import app
except Exception as e:
    import traceback
    _import_error = str(e)
    _import_traceback = traceback.format_exc()

    # Create a fallback FastAPI app that reports the error
    app = _create_fallback_app(_import_error, _import_traceback)

# For Vercel compatibility, also provide the app as 'handler'
handler = app
