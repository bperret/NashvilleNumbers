"""
Vercel Serverless Function Handler for Nashville Numbers Converter

This module serves as the entry point for the Vercel serverless function.
Vercel's Python runtime has native ASGI support, so we can directly
export the FastAPI app without needing an adapter like Mangum.
"""

import sys
from pathlib import Path

# Ensure backend module can be imported by adding project root to Python path
# In Vercel's serverless environment, we need to explicitly set the path
project_root = Path(__file__).resolve().parent.parent
cwd = Path.cwd()

for path in [project_root, cwd]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# Import and directly export the FastAPI app
# Vercel's Python runtime will automatically handle ASGI apps
from backend.app.main import app

# For Vercel compatibility, also provide the app as 'handler'
handler = app
