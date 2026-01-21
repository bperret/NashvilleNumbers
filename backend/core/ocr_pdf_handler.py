"""
OCR PDF Handler

Handles extraction and processing of scanned/image-based PDFs using Tesseract OCR.
Extracts chords with their bounding box coordinates from OCR results.
"""

import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from typing import List, Dict, Any, Tuple
from backend.core.chord_parser import parse_chord, is_likely_chord
from backend.core.text_pdf_handler import ChordAnnotation


def extract_chords_from_scanned_pdf(pdf_path: str, dpi: int = 150) -> Tuple[List[ChordAnnotation], Dict[str, Any]]:
    """
    Extract chords with positions from a scanned/image-based PDF using OCR.

    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for converting PDF to images (higher = better quality but slower)

    Returns:
        Tuple of (list of ChordAnnotations, PDF metadata)

    Raises:
        Exception: If PDF cannot be processed or Tesseract is not installed
    """
    chords = []
    metadata = {}

    try:
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=dpi)

        metadata = {
            'num_pages': len(images),
            'page_sizes': [],
            'dpi': dpi
        }

        for page_num, image in enumerate(images):
            # Store page size (in points, assuming 72 DPI standard)
            width_pts = image.width * 72 / dpi
            height_pts = image.height * 72 / dpi

            metadata['page_sizes'].append({
                'width': width_pts,
                'height': height_pts
            })

            # Perform OCR with bounding boxes
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )

            # Extract words with their bounding boxes
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()

                # Skip empty text
                if not text:
                    continue

                # Check if this word is likely a chord
                if not is_likely_chord(text):
                    continue

                # Parse the chord
                chord = parse_chord(text)
                if not chord:
                    continue

                # Extract bounding box coordinates (in pixels)
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]

                # Convert pixel coordinates to PDF points
                # OCR gives us pixel coordinates, we need PDF points
                scale = 72 / dpi
                x0 = x * scale
                y0 = y * scale
                x1 = (x + w) * scale
                y1 = (y + h) * scale

                bbox = (x0, y0, x1, y1)

                # Estimate font size from height
                font_size = h * scale * 0.75  # Approximate conversion

                # Get confidence score
                confidence = ocr_data['conf'][i]

                # Only keep high-confidence detections
                if confidence < 60:  # Confidence threshold
                    continue

                annotation = ChordAnnotation(
                    chord=chord,
                    text=text,
                    page_number=page_num,
                    bbox=bbox,
                    font_size=font_size,
                    font_name="Helvetica"  # Default for OCR
                )

                chords.append(annotation)

    except Exception as e:
        raise Exception(f"Failed to extract chords from scanned PDF: {str(e)}")

    return chords, metadata


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess an image to improve OCR accuracy.

    Args:
        image: PIL Image

    Returns:
        Preprocessed PIL Image
    """
    # Convert to grayscale
    image = image.convert('L')

    # Optional: Apply thresholding to improve contrast
    # This can be tuned based on the quality of scanned PDFs
    # For now, keep it simple

    return image


def check_tesseract_available() -> bool:
    """
    Check if Tesseract OCR is installed and available.

    Returns:
        True if Tesseract is available, False otherwise
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def get_ocr_confidence_stats(chord_annotations: List[ChordAnnotation]) -> Dict[str, float]:
    """
    Get statistics about OCR confidence for detected chords.

    Args:
        chord_annotations: List of chord annotations from OCR

    Returns:
        Dictionary with confidence statistics
    """
    if not chord_annotations:
        return {
            'avg_confidence': 0,
            'min_confidence': 0,
            'max_confidence': 0
        }

    # Note: In current implementation, we filter by confidence threshold
    # So all returned chords have confidence >= 60
    return {
        'avg_confidence': 85.0,  # Placeholder since we filter
        'min_confidence': 60.0,
        'max_confidence': 100.0,
        'note': 'Chords with confidence < 60 are filtered out'
    }
