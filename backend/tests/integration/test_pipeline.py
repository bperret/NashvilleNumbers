"""
Integration Tests for Complete Pipeline

Tests end-to-end conversion with golden file validation.
"""

import pytest
import json
from pathlib import Path
import uuid

from backend.app.models import ConversionRequest, ConversionMode
from backend.app.config import TEMP_DIR
from backend.pipeline.processor import NashvillePipeline
from backend.utils.cleanup import TempFileManager

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures'
INPUT_DIR = FIXTURES_DIR / 'input'
EXPECTED_DIR = FIXTURES_DIR / 'expected'
OUTPUT_DIR = FIXTURES_DIR / 'output'

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EXPECTED_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def temp_manager():
    """Provide temp file manager for tests"""
    return TempFileManager(TEMP_DIR, ttl_minutes=15)


@pytest.fixture
def pipeline(temp_manager):
    """Provide pipeline instance"""
    return NashvillePipeline(temp_manager)


class TestPipelineIntegration:
    """Test complete pipeline with real PDFs"""

    def test_simple_pdf_conversion(self, pipeline):
        """Test conversion of simple PDF with basic chords"""
        pdf_path = INPUT_DIR / 'sample_simple.pdf'

        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")

        # Read PDF
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        # Create request
        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key='G',
            mode=ConversionMode.MAJOR,
        )

        # Process
        result, output_path = pipeline.process(pdf_bytes, request)

        # Assert success
        assert result.success, f"Conversion failed: {result.error.message if result.error else 'Unknown'}"
        assert output_path is not None
        assert output_path.exists()

        # Verify statistics
        assert result.total_tokens_extracted > 0
        assert result.total_chords_identified > 0
        assert result.total_chords_converted > 0
        assert result.processing_time_seconds > 0

        # Check expected conversions for G major
        # G → 1, C → 4, D → 5, Em → 6m, etc.
        assert result.total_chords_converted >= 15  # Should have at least 15 chords

    def test_complex_chords_conversion(self, pipeline):
        """Test conversion with complex chord types"""
        pdf_path = INPUT_DIR / 'sample_complex.pdf'

        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key='C',
            mode=ConversionMode.MAJOR,
        )

        result, output_path = pipeline.process(pdf_bytes, request)

        assert result.success
        assert output_path.exists()

        # Should handle maj7, 7, slash chords, etc.
        assert result.total_chords_converted >= 20

    def test_multipage_pdf(self, pipeline):
        """Test conversion of multi-page PDF"""
        pdf_path = INPUT_DIR / 'sample_multipage.pdf'

        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key='C',
            mode=ConversionMode.MAJOR,
        )

        result, output_path = pipeline.process(pdf_bytes, request)

        assert result.success
        assert output_path.exists()

        # Should process all pages
        assert result.pdf_metadata.num_pages == 3
        assert result.total_chords_converted >= 10

    @pytest.mark.parametrize('key,mode', [
        ('C', 'major'),
        ('G', 'major'),
        ('D', 'major'),
        ('A', 'major'),
        ('E', 'major'),
        ('Am', 'minor'),
        ('Dm', 'minor'),
    ])
    def test_different_keys(self, pipeline, key, mode):
        """Test conversion in different keys"""
        pdf_path = INPUT_DIR / 'sample_simple.pdf'

        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key=key,
            mode=ConversionMode(mode),
        )

        result, output_path = pipeline.process(pdf_bytes, request)

        assert result.success, f"Failed for key {key} {mode}: {result.error.message if result.error else 'Unknown'}"
        assert output_path.exists()


class TestGoldenFiles:
    """Test with golden file comparisons"""

    def test_golden_conversion_metadata(self, pipeline):
        """Test that conversion produces expected metadata"""
        pdf_path = INPUT_DIR / 'sample_simple.pdf'
        golden_path = EXPECTED_DIR / 'sample_simple_G_major.json'

        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key='G',
            mode=ConversionMode.MAJOR,
        )

        result, output_path = pipeline.process(pdf_bytes, request)

        assert result.success

        # Create golden file if it doesn't exist
        if not golden_path.exists():
            golden_data = {
                "key": result.key,
                "mode": result.mode,
                "total_tokens_extracted": result.total_tokens_extracted,
                "total_chords_identified": result.total_chords_identified,
                "total_chords_converted": result.total_chords_converted,
            }
            with open(golden_path, 'w') as f:
                json.dump(golden_data, f, indent=2)
            pytest.skip("Golden file created, re-run test to validate")

        # Load golden file and compare
        with open(golden_path, 'r') as f:
            golden_data = json.load(f)

        assert result.key == golden_data["key"]
        assert result.mode == golden_data["mode"]

        # Allow some tolerance for token/chord counts
        # (pdfplumber might extract slightly different tokens across versions)
        assert abs(result.total_chords_identified - golden_data["total_chords_identified"]) <= 2


class TestErrorHandling:
    """Test error handling in pipeline"""

    def test_invalid_pdf(self, pipeline):
        """Test handling of invalid PDF"""
        # Create fake PDF bytes
        invalid_bytes = b"This is not a PDF"

        request = ConversionRequest(
            correlation_id=str(uuid.uuid4()),
            key='C',
            mode=ConversionMode.MAJOR,
        )

        result, output_path = pipeline.process(invalid_bytes, request)

        assert not result.success
        assert result.error is not None
        assert "not a valid PDF" in result.error.message.lower()

    def test_empty_pdf(self, pipeline):
        """Test handling of PDF with no chords"""
        # Would need a PDF with no chords
        pytest.skip("Requires PDF fixture with no chords")

    def test_scanned_pdf(self, pipeline):
        """Test that scanned PDFs are rejected"""
        # Would need a scanned PDF fixture
        pytest.skip("Requires scanned PDF fixture")
