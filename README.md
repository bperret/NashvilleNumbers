# Nashville Numbers Converter

A web application that converts chord chart PDFs to Nashville Number System format, preserving the original layout as closely as possible.

Built for worship band musicians (especially bass players) who need to quickly convert chord charts to numbers for easier transposition and reading.

## Features

- **PDF Upload**: Drag-and-drop or click to upload chord chart PDFs
- **Smart Detection**: Automatically detects text-based vs scanned PDFs
- **OCR Support**: Handles scanned PDFs using Tesseract OCR
- **Nashville Conversion**: Converts chord symbols (C, Dm, G7, etc.) to Nashville numbers (1, 2m, 5/7, etc.)
- **Layout Preservation**: Maintains original fonts, spacing, and positioning
- **Key Selection**: Support for all major and minor keys
- **Quality Support**: Handles maj7, 7th, sus, dim, aug, add9, slash chords, and more
- **Privacy First**: No permanent storage, files deleted after 15 minutes

## Deployment

**Note**: This app requires system dependencies (Tesseract OCR, poppler-utils) that Vercel doesn't support. For production deployment, use a **hybrid approach**:

- **Frontend** → Vercel (static site)
- **Backend** → Railway/Render/Fly.io (Docker support)

📖 **See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions**

### Quick Deploy

1. **Deploy Backend to Railway:**
   - Connect your GitHub repo at https://railway.app
   - Railway auto-detects the Dockerfile
   - Copy your Railway URL (e.g., `https://your-app.up.railway.app`)

2. **Deploy Frontend to Vercel:**
   ```bash
   vercel --prod
   ```

3. **Configure API URL:**
   - Edit `frontend/config.js`
   - Set `window.BACKEND_URL = 'https://your-railway-url.com'`
   - Redeploy to Vercel

4. **Update CORS:**
   - Edit `backend/api/main.py` line 38
   - Add your Vercel domain to `allow_origins`

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NashvilleNumbers
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Stop the application**
   ```bash
   docker-compose down
   ```

### Local Development (Without Docker)

1. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils

   # macOS
   brew install tesseract poppler
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend**
   ```bash
   uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Serve the frontend**
   ```bash
   # Option 1: Using Python
   cd frontend
   python -m http.server 3000

   # Option 2: Using any static file server
   # Then open index.html in your browser
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

## Usage

1. **Upload a PDF**: Drag and drop or click to select a chord chart PDF
2. **Select Key**: Choose the song key from the dropdown (e.g., "G")
3. **Select Mode**: Choose Major or Minor
4. **Convert**: Click "Convert to Nashville Numbers"
5. **Download**: Your converted PDF will download automatically

### Example Conversions

In the key of **C Major**:
- `C` → `1`
- `Dm` → `2m`
- `Em` → `3m`
- `F` → `4`
- `G` → `5`
- `Am` → `6m`
- `G7` → `57`
- `Cmaj7` → `1maj7`
- `G/B` → `5/7`
- `D/F#` → `2/4#` (chromatic)

In the key of **G Major**:
- `G` → `1`
- `Am` → `2m`
- `Bm` → `3m`
- `C` → `4`
- `D` → `5`
- `Em` → `6m`

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Processing**: pdfplumber (text extraction), reportlab (PDF generation)
- **OCR**: Tesseract + pytesseract
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Docker + docker-compose

### Data Flow

```
User uploads PDF
      ↓
Backend receives file
      ↓
Detect PDF type (text vs scanned)
      ↓
┌─────────────┬─────────────┐
│ Text PDF    │ Scanned PDF │
│ pdfplumber  │ Tesseract   │
└─────────────┴─────────────┘
      ↓
Extract chords with bounding boxes
      ↓
Parse chord symbols (regex)
      ↓
Convert to Nashville numbers (music theory)
      ↓
Render new PDF with numbers at original positions
      ↓
Return converted PDF to user
```

### Module Structure

```
nashville_converter/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI app and endpoints
│   ├── core/
│   │   ├── chord_parser.py      # Chord regex and parsing
│   │   ├── nashville_converter.py # Music theory conversion
│   │   ├── text_pdf_handler.py  # Text-based PDF processing
│   │   ├── ocr_pdf_handler.py   # Scanned PDF + OCR
│   │   ├── pdf_renderer.py      # Output PDF generation
│   │   └── pdf_processor.py     # Main orchestrator
│   └── tests/
│       ├── test_chord_parser.py
│       └── test_nashville_converter.py
├── frontend/
│   └── index.html               # Upload UI
├── ARCHITECTURE.md              # Detailed architecture docs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Running Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_chord_parser.py -v

# Run with coverage
pytest backend/tests/ --cov=backend/core --cov-report=html
```

All 79 tests should pass ✓

## API Documentation

### Endpoints

#### `POST /convert`
Convert a chord chart PDF to Nashville Number System.

**Request:**
- `file`: PDF file (multipart/form-data)
- `key`: Musical key (e.g., "C", "G", "Bb")
- `mode`: "major" or "minor"

**Response:**
- Returns converted PDF file
- Headers include conversion statistics

**Example with curl:**
```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@chord_chart.pdf" \
  -F "key=G" \
  -F "mode=major" \
  --output nashville_chart.pdf
```

#### `GET /keys`
Get list of supported musical keys.

**Response:**
```json
{
  "keys": ["C", "C#", "Db", "D", ...]
}
```

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "capabilities": {
    "text_pdf_support": true,
    "ocr_support": true,
    "supported_keys": [...],
    "supported_modes": ["major", "minor"]
  }
}
```

## Known Limitations

### MVP Scope
1. **Chord Detection**: Regex-based pattern matching may miss unusual chord symbols or misidentify words as chords
2. **Font Matching**: Best-effort font replication; exact fonts not always available
3. **Layout Precision**: Complex multi-column layouts may have minor positioning errors
4. **OCR Accuracy**: Scanned PDF quality directly impacts chord detection accuracy
5. **No Auto-Key Detection**: User must manually specify the song key
6. **Single File**: Processes one PDF at a time (no batch mode)
7. **File Size**: 10 MB maximum per PDF

### Edge Cases
- **Ambiguous Text**: Single-letter words like "A" could be chords or lyrics
- **Handwritten Charts**: Not supported (requires clean scanned text)
- **Encrypted PDFs**: Cannot be processed
- **Non-Standard Notation**: Jazz symbols like ø, △ may not be recognized
- **Transposition**: Tool converts to Nashville, but doesn't transpose keys

## Troubleshooting

### "No chords detected"
- Ensure PDF contains actual chord symbols (C, Dm, G7, etc.)
- Try uploading a clearer scan if using a scanned PDF
- Check that PDF is not encrypted or password-protected

### "OCR not available"
- Install Tesseract: `sudo apt-get install tesseract-ocr` (Linux) or `brew install tesseract` (Mac)
- Rebuild Docker image if using containers

### "File too large"
- Current limit is 10 MB per PDF
- Consider splitting multi-song books into individual charts

### Font rendering issues
- The app uses closest available system fonts
- Some specialty fonts may not render identically
- Numbers are positioned at original chord locations

## Future Enhancements

- [ ] Batch processing (multiple PDFs)
- [ ] Auto key detection using ML/heuristics
- [ ] Export to ChordPro format
- [ ] Support for alternate tunings
- [ ] Mobile-responsive frontend
- [ ] User accounts and conversion history
- [ ] API authentication for programmatic access
- [ ] Support for more exotic chords (13th, polychords, polytonal)
- [ ] Preview before download
- [ ] Confidence scoring for detected chords

## Contributing

This is an MVP built for worship musicians. Contributions welcome!

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest backend/tests/ -v`
5. Submit a pull request

### Code Style
- Python: Follow PEP 8
- Tests: Maintain >80% coverage
- Docs: Update README and ARCHITECTURE.md for significant changes

## License

MIT License - See LICENSE file for details

## Credits

Built for worship band musicians who need quick Nashville Number conversions.

### Technologies Used
- FastAPI - Modern Python web framework
- pdfplumber - PDF text extraction
- reportlab - PDF generation
- Tesseract - OCR engine
- Docker - Containerization

## Support

For issues or questions:
- GitHub Issues: Report bugs and feature requests
- Architecture Docs: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Version**: 1.0.0 (MVP)
**Status**: Production-ready for local use
**Target Users**: Worship band musicians, music directors, bass players
