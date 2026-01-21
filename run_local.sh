#!/bin/bash
# Quick start script for local development

echo "🎵 Nashville Numbers Converter - Local Development Setup"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Check Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR not found. Scanned PDF support will be limited."
    echo "   Install: sudo apt-get install tesseract-ocr (Linux)"
    echo "           brew install tesseract (macOS)"
fi

# Start backend
echo ""
echo "🚀 Starting backend on http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""

uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
