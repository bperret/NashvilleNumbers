"""
Vercel Serverless Function Handler for Nashville Numbers Converter
"""

import sys
from pathlib import Path

# Ensure backend module can be imported by adding project root to Python path
# In Vercel's serverless environment, we need to explicitly set the path
# We try both the parent directory of the api folder and the current working directory
project_root = Path(__file__).resolve().parent.parent
cwd = Path.cwd()

for path in [project_root, cwd]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from mangum import Mangum
from backend.api.main import app

# Wrap FastAPI app with Mangum for Vercel serverless compatibility
handler = Mangum(app, lifespan="off")
