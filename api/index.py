"""
Vercel Serverless Function Handler for Nashville Numbers Converter
"""

from mangum import Mangum
from backend.api.main import app

# Wrap FastAPI app with Mangum for Vercel serverless compatibility
handler = Mangum(app, lifespan="off")
