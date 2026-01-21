# Nashville Numbers Converter - Architecture

## Overview
A web application that converts chord chart PDFs to Nashville Number System format while preserving original layout.

## Tech Stack Justification

### Backend: FastAPI (Python)
- **Why**: Modern async framework, built-in OpenAPI docs, excellent for file upload APIs
- **Alternatives considered**: Flask (less modern), Django (overkill for MVP)

### PDF Processing: pdfplumber + reportlab
- **pdfplumber**: Superior text extraction with precise bounding box coordinates
- **reportlab**: Industry standard for PDF generation with fine-grained positioning control
- **Why not pypdf**: Limited positioning metadata for text extraction

### OCR: Tesseract + pytesseract
- **Why**: Open source, battle-tested, good accuracy, supports bounding boxes
- **Alternatives**: Cloud OCR APIs (adds cost/latency), but could be future enhancement

### Frontend: Vanilla HTML/CSS/JavaScript
- **Why**: Simple upload form doesn't justify React/Vue overhead for MVP
- **Future**: Could migrate to React for richer features (batch processing, history)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ - PDF Upload (drag & drop)                           │  │
│  │ - Key Selection Dropdown (A, Bb, B...G#)             │  │
│  │ - Convert Button                                      │  │
│  │ - Download Result PDF                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ POST /convert (multipart/form-data)
                      │ {file: PDF, key: "C"}
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ POST /convert endpoint                                │  │
│  │ - Validate PDF                                        │  │
│  │ - Save to temp storage (/tmp/upload_*.pdf)           │  │
│  │ - Call PDF Processor                                  │  │
│  │ - Return converted PDF                                │  │
│  │ - Cleanup temp files (15 min TTL)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                   PDF Processor (Orchestrator)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Detect PDF type (text vs scanned)                 │  │
│  │ 2. Route to appropriate handler                       │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────┬────────────────────────────────┬─────────────┘
               │                                │
      Text-based PDF                    Scanned/Image PDF
               │                                │
               ↓                                ↓
┌──────────────────────────┐      ┌──────────────────────────┐
│  Text PDF Handler        │      │  OCR PDF Handler         │
│  - pdfplumber extract    │      │  - Convert pages to imgs │
│  - Get text + bbox       │      │  - Tesseract OCR + bbox  │
│  - Identify chords       │      │  - Identify chords       │
└──────────────┬───────────┘      └──────────┬───────────────┘
               │                             │
               └──────────┬──────────────────┘
                          ↓
               ┌────────────────────────┐
               │   Chord Parser         │
               │   - Regex matching     │
               │   - Validate chord     │
               └──────────┬─────────────┘
                          ↓
               ┌────────────────────────┐
               │ Nashville Converter    │
               │ - Key to scale degree  │
               │ - Quality preservation │
               │ - Slash chord handling │
               └──────────┬─────────────┘
                          ↓
               ┌────────────────────────┐
               │  PDF Renderer          │
               │  - reportlab canvas    │
               │  - Place numbers at    │
               │    original positions  │
               │  - Match fonts/size    │
               └──────────┬─────────────┘
                          ↓
                    Output PDF
```

## Data Flow

### 1. Upload Phase
```
User → Frontend → Backend
- File: chord_chart.pdf
- Key: "G"
- (Optional: minor/major mode)
```

### 2. Processing Phase
```python
# Simplified pseudocode
pdf_bytes = await file.read()
temp_path = save_temp(pdf_bytes)

# Detect PDF type
is_text_based = has_extractable_text(temp_path)

if is_text_based:
    chords = extract_text_chords(temp_path)  # [{text: "C", bbox: (x,y,w,h), page: 0}]
else:
    chords = extract_ocr_chords(temp_path)   # Same structure

# Convert chords
converted = []
for chord in chords:
    nashville_num = convert_to_nashville(chord.text, key="G")
    converted.append({...chord, nashville: nashville_num})

# Render new PDF
output_pdf = render_pdf(original_pdf, converted_chords)
return output_pdf
```

### 3. Rendering Strategy

**Text-based PDFs**:
- Extract page as PDF → render as background
- Overlay white rectangles over original chord positions
- Draw Nashville numbers in closest matching font

**Scanned PDFs**:
- Keep original page as image background
- Draw white rectangles over detected chord regions
- Render Nashville numbers at detected positions

## Module Breakdown

### 1. `chord_parser.py`
**Responsibility**: Identify and parse chord symbols from text

```python
# Regex patterns for chords
CHORD_PATTERN = r'\b([A-G][b#]?)(maj|min|m|dim|aug|sus)?([0-9]*)([b#]?[0-9]*)?(add[0-9]+)?(/[A-G][b#]?)?\b'

def parse_chord(text: str) -> Optional[Chord]:
    """Parse a chord string into components"""
    # Returns: Chord(root="C", quality="maj7", extensions="", bass="E")

def is_likely_chord(text: str, bbox: BBox) -> bool:
    """Heuristic to distinguish chords from lyrics"""
    # - Matches chord regex
    # - Position above lyrics line
    # - Short length (< 10 chars)
```

### 2. `nashville_converter.py`
**Responsibility**: Music theory conversion logic

```python
# Scale degree mappings
MAJOR_SCALE = {'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'A': 6, 'B': 7}
CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def convert_chord_to_nashville(chord: Chord, key: str, mode: str = "major") -> str:
    """
    Convert chord to Nashville number
    Examples:
    - C in key of C → "1"
    - Dm in key of C → "2m"
    - Cmaj7 in key of C → "1maj7"
    - G/B in key of C → "5/3"
    """

def calculate_scale_degree(root: str, key: str) -> int:
    """Calculate scale degree using chromatic distance"""
    # Handle enharmonics (C# = Db)
```

### 3. `pdf_processor.py`
**Responsibility**: Orchestrate the conversion pipeline

```python
async def process_pdf(pdf_path: str, key: str) -> bytes:
    """Main conversion pipeline"""
    # 1. Detect PDF type
    # 2. Extract chords
    # 3. Convert to Nashville
    # 4. Render output
    # 5. Return bytes
```

### 4. `text_pdf_handler.py`
**Responsibility**: Handle text-based PDFs

```python
def extract_chords_from_text_pdf(pdf_path: str) -> List[ChordAnnotation]:
    """Use pdfplumber to extract text with positions"""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            # Filter and identify chords
```

### 5. `ocr_pdf_handler.py`
**Responsibility**: Handle scanned PDFs

```python
def extract_chords_from_scanned_pdf(pdf_path: str) -> List[ChordAnnotation]:
    """Use Tesseract OCR with bounding boxes"""
    images = convert_from_path(pdf_path)
    for img in images:
        data = pytesseract.image_to_data(img, output_type=Output.DICT)
        # Extract chords from OCR results
```

## Key Design Decisions

### 1. Chord Detection Heuristics
Since we don't have AI/ML chord recognition, we use:
- **Regex matching**: Strong pattern for chord symbols
- **Positional logic**: Chords typically appear above lyrics or in dedicated rows
- **Font size**: Chords often slightly smaller or same size as lyrics
- **Spacing**: Isolated tokens with whitespace around them

### 2. Slash Chord Notation
**Decision**: Use `5/3` format (scale degree/bass scale degree)
- More compact than `V/iii`
- Easier to parse programmatically
- Common in modern Nashville charts

### 3. Minor vs Major Key Detection
**MVP Decision**: User must specify key
- **Future**: Auto-detect by analyzing chord patterns (presence of flat-3, flat-7, etc.)

### 4. Font Matching Strategy
1. Try to extract original font name from PDF metadata
2. Map to closest system font (Helvetica, Arial, Times)
3. Preserve font size from original chord
4. Fall back to Arial if no match

### 5. Privacy & Storage
- Upload saved to `/tmp/{uuid}.pdf` with 15-minute TTL
- Background cleanup task deletes files > 15 min old
- No database, no persistent storage
- No logging of PDF content

## Error Handling

### Graceful Degradation
1. **No chords detected**: Return error with suggestion to use OCR mode
2. **Ambiguous chords**: Flag in output, keep original
3. **Key mismatch**: If user selects C but chords suggest G, warn but proceed
4. **Font unavailable**: Use fallback font, note in response

### User-Facing Errors
- "No chords detected in PDF. Ensure the PDF contains chord symbols."
- "Could not parse chord: [XYZ]. Please verify chord notation."
- "Key must be one of: A, A#, Bb, B, C, C#, Db, D, D#, Eb, E, F, F#, Gb, G, G#, Ab"

## Testing Strategy

### Unit Tests
- `test_chord_parser.py`: Regex matching, chord validation
- `test_nashville_converter.py`: All conversions, edge cases

### Integration Tests
- Sample text-based PDF → verify output
- Sample scanned PDF → verify OCR path
- Edge case PDFs (multi-column, small fonts)

### Test Fixtures
```
tests/fixtures/
├── simple_text.pdf (C-Am-F-G in key of C)
├── scanned.pdf (image-based)
├── complex_chords.pdf (Cmaj7, D/F#, Gsus4)
└── multi_column.pdf
```

## Known Limitations (for README)

1. **Chord Detection**: Regex-based, may miss unusual chord symbols or mis-identify lyrics
2. **Font Matching**: Best-effort; exact font replication not guaranteed
3. **Layout Preservation**: Complex multi-column layouts may have positioning errors
4. **OCR Accuracy**: Scanned PDFs depend on image quality; low-res scans may fail
5. **No Auto-Key Detection**: User must manually specify key for MVP
6. **Single Page Focus**: Multi-page PDFs processed page-by-page but not optimized for books
7. **No Transposition**: Only converts to Nashville; doesn't transpose keys

## Future Enhancements

- Batch processing (multiple PDFs)
- Auto key detection using ML
- Support for alternate tunings (DADGAD, drop D)
- Export to ChordPro format
- Chord diagram generation
- User accounts with conversion history
- API key for programmatic access
- Support for more exotic chord types (13th, polychords)

## Performance Targets (MVP)

- Single page text PDF: < 2 seconds
- Single page scanned PDF: < 5 seconds (OCR bottleneck)
- Max file size: 10 MB
- Concurrent requests: 5 (can be scaled with workers)

## Security Considerations

- File upload validation (PDF MIME type, magic bytes)
- Max file size enforcement (10 MB)
- Temp file isolation (unique UUIDs)
- No shell command injection (use Python libraries only)
- CORS configured for frontend origin only
