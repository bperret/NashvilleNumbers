# PDF Generation Testing Suite

This directory contains tools and tests for iteratively testing the Nashville Number System PDF converter.

## Overview

The testing suite provides multiple ways to test PDF generation:

1. **Interactive Test Runner** - For manual, iterative testing with detailed diagnostics
2. **Pytest Test Suite** - For automated testing and CI/CD integration
3. **Sample PDFs** - Pre-generated test fixtures for immediate testing

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Sample Test PDFs

```bash
cd backend
python tests/create_sample_pdf.py
```

This creates three test PDFs:
- `sample_simple.pdf` - Simple chord chart (Amazing Grace)
- `sample_complex.pdf` - Various chord types (major, minor, 7ths, altered, slash chords)
- `sample_multipage.pdf` - Multi-page document

### 3. Run the Interactive Test Runner

```bash
cd backend
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf
```

## Interactive Test Runner

The `test_pdf_runner.py` script provides detailed diagnostics and is perfect for iterative development.

### Basic Usage

```bash
# Test with defaults (C major)
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf

# Test with specific key
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf --key G --mode major

# Verbose output with full diagnostics
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf -v

# Specify custom output location
python tests/test_pdf_runner.py input.pdf -o output.pdf
```

### Command-Line Options

```
positional arguments:
  input                 Input PDF file path

optional arguments:
  -h, --help            show this help message and exit
  -k KEY, --key KEY     Musical key (default: C)
  -m {major,minor}, --mode {major,minor}
                        Musical mode (default: major)
  -o OUTPUT, --output OUTPUT
                        Output PDF path (default: tests/fixtures/output/<input>_nashville.pdf)
  -v, --verbose         Show verbose output with detailed diagnostics
```

### What It Shows

The test runner provides:
- Input validation (file exists, size check, format)
- Processing status with timing
- Detailed statistics:
  - PDF type (text vs scanned)
  - Pages processed
  - Chords found and converted
  - Render quality metrics
  - OCR confidence (for scanned PDFs)
- Output file verification
- Color-coded success/error messages
- Full error tracebacks (with `-v`)

### Example Output

```
======================================================================
                          PDF Test Runner
======================================================================

Input:  /path/to/tests/fixtures/input/sample_simple.pdf
Output: /path/to/tests/fixtures/output/sample_simple_nashville.pdf
Key:    C major
Verbose: False
✓ Input file validated: sample_simple.pdf (0.02 MB)

======================================================================
                       Starting PDF Processing
======================================================================

ℹ Initializing PDF processor...
ℹ Processing: sample_simple.pdf
ℹ Key: C major
ℹ Output: sample_simple_nashville.pdf

======================================================================
                       Processing Successful
======================================================================

✓ Processing completed in 1.23 seconds
✓ Output file created: sample_simple_nashville.pdf (24.5 KB)

======================================================================
                           Final Status
======================================================================

✓ PDF processing completed successfully!

Output: /path/to/tests/fixtures/output/sample_simple_nashville.pdf
```

## Automated Testing with Pytest

For automated testing and CI/CD:

```bash
cd backend
pytest tests/test_pdf_generation.py -v
```

### Test Categories

The pytest suite includes:

1. **TestPDFProcessor** - Main processor tests
   - Initialization
   - Text PDF processing
   - Multiple key conversions
   - Invalid input handling

2. **TestTextPDFHandler** - Text extraction tests
   - PDF type detection
   - Chord extraction from text PDFs

3. **TestPDFRenderer** - Rendering tests
   - Nashville number overlay rendering

4. **TestEndToEndProcessing** - Integration tests
   - Complete workflow testing
   - Multiple key/mode combinations

5. **TestErrorHandling** - Edge cases
   - Empty PDFs
   - Corrupted PDFs
   - Oversized PDFs

### Running Specific Tests

```bash
# Run all tests
pytest tests/test_pdf_generation.py

# Run specific test class
pytest tests/test_pdf_generation.py::TestPDFProcessor

# Run specific test
pytest tests/test_pdf_generation.py::TestPDFProcessor::test_process_text_pdf

# Run with verbose output
pytest tests/test_pdf_generation.py -v

# Run with output capture disabled (see print statements)
pytest tests/test_pdf_generation.py -s
```

### Manual Testing Helper

The test suite includes a helper function for manual testing:

```python
from tests.test_pdf_generation import test_specific_pdf

# Test any PDF file
result = test_specific_pdf('path/to/my.pdf', key='G', mode='major')
```

## Directory Structure

```
tests/
├── README.md                    # This file
├── test_pdf_runner.py          # Interactive test runner
├── test_pdf_generation.py      # Pytest test suite
├── create_sample_pdf.py        # Sample PDF generator
├── fixtures/
│   ├── input/                  # Test input PDFs
│   │   ├── sample_simple.pdf
│   │   ├── sample_complex.pdf
│   │   └── sample_multipage.pdf
│   └── output/                 # Test output PDFs (generated)
│       └── *.pdf
├── test_chord_parser.py        # Existing chord parser tests
└── test_nashville_converter.py # Existing converter tests
```

## Iterative Testing Workflow

Here's a typical workflow for debugging and fixing issues:

### 1. Run Test and Identify Issue

```bash
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf -v
```

Look for:
- Error messages
- Failed chord extractions
- Incorrect conversions
- Rendering issues

### 2. Make Code Changes

Edit the relevant files in `backend/core/`:
- `pdf_processor.py` - Main orchestration
- `text_pdf_handler.py` - Text PDF extraction
- `ocr_pdf_handler.py` - Scanned PDF extraction
- `pdf_renderer.py` - PDF rendering
- `chord_parser.py` - Chord parsing
- `nashville_converter.py` - Nashville conversion

### 3. Re-run Test

```bash
python tests/test_pdf_runner.py tests/fixtures/input/sample_simple.pdf -v
```

### 4. Repeat Until Success

Keep iterating until the test passes!

### 5. Run Full Test Suite

Once working, run the full pytest suite:

```bash
pytest tests/test_pdf_generation.py -v
```

## Testing with Your Own PDFs

### Add Your PDF to Fixtures

```bash
cp your_file.pdf backend/tests/fixtures/input/
```

### Test It

```bash
python tests/test_pdf_runner.py tests/fixtures/input/your_file.pdf -v
```

### Test Different Keys

```bash
# Test in G major
python tests/test_pdf_runner.py tests/fixtures/input/your_file.pdf --key G

# Test in A minor
python tests/test_pdf_runner.py tests/fixtures/input/your_file.pdf --key A --mode minor

# Test all common keys
for key in C D E F G A B; do
    echo "Testing key: $key"
    python tests/test_pdf_runner.py tests/fixtures/input/your_file.pdf --key $key
done
```

## Troubleshooting

### "No module named 'reportlab'"

Install dependencies:
```bash
pip install -r requirements.txt
```

### "Sample PDF not found"

Generate sample PDFs:
```bash
python tests/create_sample_pdf.py
```

### "Tesseract not found" (for scanned PDFs)

Install Tesseract OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Output PDF is empty or incorrect

Enable verbose mode to see detailed diagnostics:
```bash
python tests/test_pdf_runner.py input.pdf -v
```

Check:
- Chord extraction count
- Conversion success rate
- Render quality metrics
- Font matching
- OCR confidence (for scanned PDFs)

## CI/CD Integration

Add to your CI pipeline:

```yaml
# Example for GitHub Actions
- name: Run PDF Tests
  run: |
    cd backend
    pytest tests/test_pdf_generation.py -v --tb=short
```

## Tips for Effective Testing

1. **Start Simple** - Begin with `sample_simple.pdf` before moving to complex charts
2. **Use Verbose Mode** - Always use `-v` when debugging to see full diagnostics
3. **Test Multiple Keys** - Test conversions in different keys to catch key-specific bugs
4. **Keep Output Files** - Review generated PDFs in `fixtures/output/` to verify visual quality
5. **Add Your Own PDFs** - Test with real-world chord charts from your use case
6. **Automate Regression Tests** - Add new test cases to `test_pdf_generation.py` for bugs you fix

## Contributing

When adding new features or fixing bugs:

1. Add test cases to `test_pdf_generation.py`
2. Create new fixture PDFs if needed
3. Update this README with new capabilities
4. Ensure all tests pass before committing

## Support

For issues or questions:
- Check the main project README
- Review error messages in verbose mode
- Examine the generated output PDFs
- Check the test logs in `fixtures/output/`
