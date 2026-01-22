"""
Vercel Serverless Function Handler for Nashville Numbers Converter
"""

from backend.api.main import app

# Export the FastAPI app as 'handler' for Vercel
handler = app
