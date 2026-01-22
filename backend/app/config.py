"""
Configuration for Nashville Numbers Converter
"""

import os
from pathlib import Path
from typing import List

# Application settings
APP_NAME = "Nashville Numbers Converter"
APP_VERSION = "2.0.0"

# File storage
TEMP_DIR = Path(os.getenv("TEMP_DIR", "/tmp/nashville_converter"))
TEMP_FILE_TTL_MINUTES = int(os.getenv("TEMP_FILE_TTL_MINUTES", "15"))

# File limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# PDF processing
PDF_DPI = int(os.getenv("PDF_DPI", "72"))
MIN_TEXT_THRESHOLD = int(os.getenv("MIN_TEXT_THRESHOLD", "50"))

# Chord detection
CHORD_CONFIDENCE_THRESHOLD = float(os.getenv("CHORD_CONFIDENCE_THRESHOLD", "0.8"))
MIN_FONT_SIZE = float(os.getenv("MIN_FONT_SIZE", "8"))
MAX_FONT_SIZE = float(os.getenv("MAX_FONT_SIZE", "24"))

# Supported keys
SUPPORTED_KEYS: List[str] = [
    'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F',
    'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B'
]

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_DEBUG_MODE = os.getenv("ENABLE_DEBUG_MODE", "false").lower() == "true"

def ensure_temp_dir():
    """Ensure temp directory exists"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
