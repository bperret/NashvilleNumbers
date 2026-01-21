"""
Vercel Serverless Function Entry Point

This module wraps the FastAPI application for deployment on Vercel's
serverless platform. It imports the main FastAPI app and exports it
as a handler function that Vercel can invoke.
"""

from backend.api.main import app

# Export the FastAPI app as a Vercel serverless handler
# Vercel will automatically detect and route requests to this handler
handler = app
