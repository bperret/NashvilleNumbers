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

try:
    # Import and directly export the FastAPI app
    # Vercel's Python runtime will automatically handle ASGI apps
    from backend.api.main import app
except Exception as e:
    import traceback
    _import_error = str(e)
    _import_traceback = traceback.format_exc()

    # Create a fallback FastAPI app that reports the error
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Nashville Numbers Converter - Error Mode")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    @app.get("/api/")
    async def error_root():
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Failed to import main application",
                "import_error": _import_error,
                "traceback": _import_traceback,
                "sys_path": sys.path[:10],
                "cwd": str(cwd),
                "project_root": str(project_root),
            }
        )

    @app.get("/diagnostics")
    @app.get("/api/diagnostics")
    async def error_diagnostics():
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Main application failed to import",
                "import_error": _import_error,
                "traceback": _import_traceback,
                "python_version": sys.version,
                "sys_path": sys.path[:10],
                "env_vars": {
                    k: v for k, v in os.environ.items()
                    if k.startswith(("PYTHON", "PATH", "VERCEL", "AWS"))
                }
            }
        )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "Main application failed to import",
                "requested_path": path,
                "import_error": _import_error,
            }
        )

# For Vercel compatibility, also provide the app as 'handler'
handler = app
