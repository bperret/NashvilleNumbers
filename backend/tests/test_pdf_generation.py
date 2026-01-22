"""
Test suite for PDF generation functionality

This module tests the complete PDF processing pipeline including:
- Text-based PDF extraction
- OCR-based PDF extraction (scanned PDFs)
- Nashville number conversion
- PDF rendering with overlays
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.pdf_processor import PDFProcessor
from backend.core.text_pdf_handler import extract_chords_from_text_pdf, detect_if_text_pdf
from backend.core.pdf_renderer import render_text_pdf_with_nashville


# Fixtures directory paths
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
INPUT_DIR = FIXTURES_DIR / 'input'
OUTPUT_DIR = FIXTURES_DIR / 'output'


@pytest.fixture(scope="session", autouse=True)
def setup_output_directory():
    """Ensure output directory exists for all tests"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after all tests (optional)
    # You may want to keep outputs for manual inspection


@pytest.fixture
def pdf_processor():
    """Provide a PDFProcessor instance"""
    return PDFProcessor()


@pytest.fixture
def sample_text_pdf():
    """
    Fixture for a sample text-based PDF
    Returns path if it exists, otherwise skips tests that need it
    """
    pdf_path = INPUT_DIR / 'sample_text.pdf'
    if not pdf_path.exists():
        pytest.skip(f"Sample text PDF not found at {pdf_path}")
    return pdf_path


@pytest.fixture
def sample_scanned_pdf():
    """
    Fixture for a sample scanned PDF
    Returns path if it exists, otherwise skips tests that need it
    """
    pdf_path = INPUT_DIR / 'sample_scanned.pdf'
    if not pdf_path.exists():
        pytest.skip(f"Sample scanned PDF not found at {pdf_path}")
    return pdf_path


class TestPDFProcessor:
    """Test the main PDF processor"""

    def test_processor_initialization(self, pdf_processor):
        """Test that PDF processor initializes correctly"""
        assert pdf_processor is not None
        assert hasattr(pdf_processor, 'process_pdf')

    def test_process_text_pdf(self, pdf_processor, sample_text_pdf):
        """Test processing a text-based PDF"""
        output_path = OUTPUT_DIR / 'test_output_text.pdf'

        result = pdf_processor.process_pdf(
            str(sample_text_pdf),
            str(output_path),
            key='C',
            mode='major'
        )

        # Verify success
        assert result['success'] is True, f"Processing failed: {result.get('error')}"

        # Verify output exists
        assert output_path.exists(), "Output PDF was not created"

        # Verify statistics
        assert result.get('pdf_type') in ['text', 'scanned']
        assert result.get('pages_processed', 0) > 0
        assert 'chords_found' in result
        assert 'chords_converted' in result

    def test_process_with_different_keys(self, pdf_processor, sample_text_pdf):
        """Test processing with different musical keys"""
        test_keys = [
            ('C', 'major'),
            ('G', 'major'),
            ('A', 'minor'),
            ('D', 'major'),
        ]

        for key, mode in test_keys:
            output_path = OUTPUT_DIR / f'test_output_{key}_{mode}.pdf'

            result = pdf_processor.process_pdf(
                str(sample_text_pdf),
                str(output_path),
                key=key,
                mode=mode
            )

            assert result['success'] is True, \
                f"Processing failed for key {key} {mode}: {result.get('error')}"
            assert output_path.exists(), \
                f"Output not created for key {key} {mode}"

    def test_invalid_input_path(self, pdf_processor):
        """Test handling of invalid input path"""
        result = pdf_processor.process_pdf(
            '/nonexistent/path/to/file.pdf',
            str(OUTPUT_DIR / 'output.pdf'),
            key='C',
            mode='major'
        )

        assert result['success'] is False
        assert 'error' in result

    def test_invalid_key(self, pdf_processor, sample_text_pdf):
        """Test handling of invalid musical key"""
        output_path = OUTPUT_DIR / 'test_invalid_key.pdf'

        result = pdf_processor.process_pdf(
            str(sample_text_pdf),
            str(output_path),
            key='InvalidKey',
            mode='major'
        )

        # Should either fail or handle gracefully
        assert 'error' in result or result['success'] is False


class TestTextPDFHandler:
    """Test text-based PDF handling"""

    def test_detect_text_pdf(self, sample_text_pdf):
        """Test detection of text-based PDFs"""
        is_text = detect_if_text_pdf(str(sample_text_pdf))
        assert isinstance(is_text, bool)

    def test_extract_chords_from_text_pdf(self, sample_text_pdf):
        """Test chord extraction from text PDFs"""
        chords = extract_chords_from_text_pdf(str(sample_text_pdf))

        assert isinstance(chords, list)

        # If chords were found, verify structure
        if len(chords) > 0:
            chord = chords[0]
            assert hasattr(chord, 'text')
            assert hasattr(chord, 'chord')
            assert hasattr(chord, 'bbox')
            assert hasattr(chord, 'page_number')
            assert hasattr(chord, 'font_size')


class TestPDFRenderer:
    """Test PDF rendering functionality"""

    def test_render_text_pdf_with_nashville(self, sample_text_pdf):
        """Test rendering Nashville numbers on text PDF"""
        from core.text_pdf_handler import extract_chords_from_text_pdf
        from core.nashville_converter import NashvilleConverter

        # Extract chords
        chord_annotations = extract_chords_from_text_pdf(str(sample_text_pdf))

        if len(chord_annotations) == 0:
            pytest.skip("No chords found in sample PDF")

        # Convert to Nashville
        converter = NashvilleConverter(key='C', mode='major')
        conversions = []

        for annotation in chord_annotations:
            try:
                nashville = converter.to_nashville(annotation.chord)
                conversions.append({
                    'original': annotation,
                    'nashville': nashville
                })
            except Exception as e:
                print(f"Failed to convert {annotation.text}: {e}")

        # Render
        output_path = OUTPUT_DIR / 'test_rendered.pdf'

        result = render_text_pdf_with_nashville(
            str(sample_text_pdf),
            conversions,
            str(output_path)
        )

        assert result['success'] is True
        assert output_path.exists()


class TestEndToEndProcessing:
    """End-to-end integration tests"""

    def test_complete_workflow_text_pdf(self, pdf_processor, sample_text_pdf):
        """Test complete workflow from PDF input to Nashville output"""
        output_path = OUTPUT_DIR / 'test_e2e_complete.pdf'

        # Process
        result = pdf_processor.process_pdf(
            str(sample_text_pdf),
            str(output_path),
            key='G',
            mode='major'
        )

        # Verify all steps completed
        assert result['success'] is True

        # Verify output quality
        assert output_path.exists()

        output_size = output_path.stat().st_size
        assert output_size > 0, "Output PDF is empty"

        # Verify metadata
        assert result.get('pages_processed', 0) > 0
        assert result.get('chords_found', 0) >= 0
        assert result.get('chords_converted', 0) >= 0

    @pytest.mark.parametrize('key,mode', [
        ('C', 'major'),
        ('D', 'major'),
        ('E', 'major'),
        ('F', 'major'),
        ('G', 'major'),
        ('A', 'minor'),
        ('B', 'minor'),
    ])
    def test_multiple_key_conversions(self, pdf_processor, sample_text_pdf, key, mode):
        """Test processing with multiple keys"""
        output_path = OUTPUT_DIR / f'test_key_{key}_{mode}.pdf'

        result = pdf_processor.process_pdf(
            str(sample_text_pdf),
            str(output_path),
            key=key,
            mode=mode
        )

        assert result['success'] is True, \
            f"Failed for {key} {mode}: {result.get('error')}"


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_pdf(self, pdf_processor):
        """Test handling of empty PDF (if we have one)"""
        empty_pdf = INPUT_DIR / 'empty.pdf'
        if not empty_pdf.exists():
            pytest.skip("No empty PDF fixture available")

        output_path = OUTPUT_DIR / 'test_empty_output.pdf'
        result = pdf_processor.process_pdf(
            str(empty_pdf),
            str(output_path),
            key='C',
            mode='major'
        )

        # Should handle gracefully
        assert 'error' in result or result['success'] is False

    def test_corrupted_pdf(self, pdf_processor):
        """Test handling of corrupted PDF"""
        corrupted_pdf = INPUT_DIR / 'corrupted.pdf'
        if not corrupted_pdf.exists():
            pytest.skip("No corrupted PDF fixture available")

        output_path = OUTPUT_DIR / 'test_corrupted_output.pdf'
        result = pdf_processor.process_pdf(
            str(corrupted_pdf),
            str(output_path),
            key='C',
            mode='major'
        )

        assert result['success'] is False
        assert 'error' in result

    def test_oversized_pdf(self, pdf_processor):
        """Test handling of oversized PDF (>10MB limit)"""
        # This would need a large PDF fixture
        pytest.skip("Oversized PDF test requires large fixture")


# Helper function to run tests on a specific PDF
def test_specific_pdf(pdf_path: str, key: str = 'C', mode: str = 'major') -> Dict[str, Any]:
    """
    Helper function to test a specific PDF file
    Useful for manual testing and debugging

    Usage:
        from tests.test_pdf_generation import test_specific_pdf
        result = test_specific_pdf('path/to/my.pdf', key='G', mode='major')
    """
    processor = PDFProcessor()
    output_path = OUTPUT_DIR / f'{Path(pdf_path).stem}_test_output.pdf'

    result = processor.process_pdf(
        pdf_path,
        str(output_path),
        key=key,
        mode=mode
    )

    print(f"\n{'=' * 70}")
    print(f"Test Results for: {Path(pdf_path).name}")
    print(f"{'=' * 70}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Output: {output_path}")
        print(f"PDF Type: {result.get('pdf_type')}")
        print(f"Pages: {result.get('pages_processed')}")
        print(f"Chords Found: {result.get('chords_found')}")
        print(f"Chords Converted: {result.get('chords_converted')}")
    else:
        print(f"Error: {result.get('error')}")
    print(f"{'=' * 70}\n")

    return result
