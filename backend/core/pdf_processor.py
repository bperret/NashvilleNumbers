"""
PDF Processor

Main orchestrator for converting chord chart PDFs to Nashville Number System.
Handles both text-based and scanned PDFs.
"""

import os
from typing import Dict, Any, List
from backend.core.text_pdf_handler import (
    extract_chords_from_text_pdf,
    detect_if_text_pdf,
    filter_false_positives
)
from backend.core.pdf_renderer import (
    render_text_pdf_with_nashville,
    estimate_render_quality
)
from backend.core.nashville_converter import (
    convert_chord_to_nashville,
    validate_key
)
from models.types import MusicKey, MusicalMode


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass


class PDFProcessor:
    """
    Main class for processing chord chart PDFs.
    """

    def __init__(self):
        """Initialize the PDF processor."""
        pass

    def process_pdf(
        self,
        input_file_bytes: bytes,
        key: MusicKey,
        mode: MusicalMode = MusicalMode.MAJOR,
        force_ocr: bool = False
    ) -> Dict[str, Any]:
        """
        Process a PDF chord chart and convert chords to Nashville numbers.

        Args:
            input_pdf_path: Path to input PDF file
            output_pdf_path: Path where output PDF will be saved
            key: Musical key (e.g., "C", "G", "Bb")
            mode: "major" or "minor"
            force_ocr: Force OCR processing even if text-based PDF detected

        Returns:
            Dictionary with processing results and statistics

        Raises:
            PDFProcessingError: If processing fails
        """
        # Check if PDF is text-based
        is_text_based = detect_if_text_pdf(input_file_bytes)

        if not is_text_based:
            raise PDFProcessingError(
                "This PDF appears to be a scanned image. Only text-based PDFs are supported. "
                "Please use a PDF with selectable text (not a scanned image)."
            )

        # Extract chords from text-based PDF
        try:
            chord_annotations, metadata = extract_chords_from_text_pdf(input_file_bytes)
            processing_method = "text_extraction"
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract chords: {str(e)}")

        # Filter false positives
        chord_annotations = filter_false_positives(chord_annotations)

        # Check if any chords were found
        if not chord_annotations:
            raise PDFProcessingError(
                "No chords detected in PDF. Please ensure the PDF contains chord symbols "
                "and is not encrypted or corrupted."
            )

        # Convert chords to Nashville numbers
        nashville_numbers = []
        conversion_errors = []

        for annotation in chord_annotations:
            try:
                nashville = convert_chord_to_nashville(annotation.chord, key, mode)
                nashville_numbers.append(nashville)
            except Exception as e:
                # If conversion fails for a specific chord, keep original
                conversion_errors.append({
                    'chord': annotation.text,
                    'error': str(e)
                })
                nashville_numbers.append(annotation.text)  # Fallback to original

        # Render output PDF
        try:
            result_file_bytes = render_text_pdf_with_nashville(
                input_file_bytes,
                chord_annotations,
                nashville_numbers,
                metadata
            )
        except Exception as e:
            raise PDFProcessingError(f"Failed to render output PDF: {str(e)}")

        # Estimate quality
        quality_metrics = estimate_render_quality(chord_annotations, metadata)

        # Return processing results
        return {
            'success': True,
            'processing_method': processing_method,
            'key': key,
            'mode': mode,
            'total_chords_found': len(chord_annotations),
            'total_chords_converted': len(nashville_numbers),
            'conversion_errors': conversion_errors,
            'quality_metrics': quality_metrics,
            'metadata': metadata,
            "result_file_bytes": result_file_bytes,
        }

    def validate_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Validate a PDF and return information about it.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF validation results
        """
        if not os.path.exists(pdf_path):
            return {
                'valid': False,
                'error': 'File not found'
            }

        # Check if it's text-based
        is_text_based = detect_if_text_pdf(pdf_path)

        if not is_text_based:
            return {
                'valid': False,
                'error': 'PDF is scanned/image-based. Only text-based PDFs are supported.',
                'is_text_based': False
            }

        # Try to extract a few chords as a test
        try:
            chords, metadata = extract_chords_from_text_pdf(pdf_path)

            return {
                'valid': True,
                'is_text_based': True,
                'num_pages': metadata.get('num_pages', 0),
                'sample_chords_found': min(len(chords), 5),
                'sample_chords': [c.text for c in chords[:5]]
            }

        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }


def get_supported_keys() -> List[str]:
    """
    Get list of supported musical keys.

    Returns:
        List of key names
    """
    return [
        'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F',
        'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B'
    ]


def get_processing_stats() -> Dict[str, Any]:
    """
    Get information about processing capabilities.

    Returns:
        Dictionary with capability information
    """
    return {
        'text_pdf_support': True,
        'ocr_support': False,
        'supported_keys': get_supported_keys(),
        'supported_modes': ['major', 'minor']
    }
