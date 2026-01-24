"""
Text PDF Handler

Handles extraction and processing of text-based PDFs using pdfplumber.
Extracts chords with their bounding box coordinates for precise replacement.
"""
import io
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from backend.core.chord_parser import parse_chord, is_likely_chord, Chord


@dataclass
class ChordAnnotation:
    """
    Represents a chord found in a PDF with its location and properties.
    """
    chord: Chord  # Parsed chord object
    text: str  # Original text
    page_number: int  # Page number (0-indexed)
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1) in PDF coordinates
    font_size: float = 12.0  # Font size in points
    font_name: str = "Helvetica"  # Font name


def extract_chords_from_text_pdf(input_file_bytes: bytes) -> Tuple[List[ChordAnnotation], Dict[str, Any]]:
    """
    Extract chords with positions from a text-based PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Tuple of (list of ChordAnnotations, PDF metadata)

    Raises:
        Exception: If PDF cannot be opened or processed
    """
    # Lazy import to avoid FUNCTION_INVOCATION_FAILED in serverless environments
    try:
        import pdfplumber
    except ImportError as e:
        raise Exception(
            "pdfplumber dependency not available. This feature requires pdfplumber. "
            f"Import error: {str(e)}"
        )

    chords = []
    metadata = {}

    try:
        with pdfplumber.open(io.BytesIO(input_file_bytes)) as pdf:
            # Extract PDF metadata
            metadata = {
                'num_pages': len(pdf.pages),
                'page_sizes': []
            }

            for page_num, page in enumerate(pdf.pages):
                try:
                    # Store page size with fallbacks
                    page_width = getattr(page, 'width', 612) or 612
                    page_height = getattr(page, 'height', 792) or 792
                    metadata['page_sizes'].append({
                        'width': page_width,
                        'height': page_height
                    })

                    # Extract words with bounding boxes
                    words = page.extract_words() or []

                    for word in words:
                        try:
                            text = word.get('text', '')
                            if not text:
                                continue

                            # Check if this word is likely a chord
                            if not is_likely_chord(text):
                                continue

                            # Parse the chord
                            chord = parse_chord(text)
                            if not chord:
                                continue

                            # Extract bounding box coordinates with defensive checks
                            # pdfplumber uses (x0, top, x1, bottom) format
                            x0 = word.get('x0')
                            top = word.get('top')
                            x1 = word.get('x1')
                            bottom = word.get('bottom')

                            # Skip if any coordinate is missing
                            if None in (x0, top, x1, bottom):
                                continue

                            bbox = (x0, top, x1, bottom)

                            # Try to extract font information with defaults
                            font_size = word.get('height') or word.get('size') or 12.0
                            font_name = word.get('fontname') or 'Helvetica'

                            # Ensure font_size is a valid number
                            try:
                                font_size = float(font_size)
                                if font_size <= 0:
                                    font_size = 12.0
                            except (TypeError, ValueError):
                                font_size = 12.0

                            annotation = ChordAnnotation(
                                chord=chord,
                                text=text,
                                page_number=page_num,
                                bbox=bbox,
                                font_size=font_size,
                                font_name=font_name
                            )

                            chords.append(annotation)

                        except Exception:
                            # Skip problematic words, continue with others
                            continue

                except Exception:
                    # Skip problematic pages, continue with others
                    continue

    except Exception as e:
        error_msg = str(e)
        if "EOF" in error_msg or "stream" in error_msg.lower():
            raise Exception(f"PDF file appears to be corrupted: {error_msg}")
        elif "encrypt" in error_msg.lower() or "password" in error_msg.lower():
            raise Exception(f"PDF file is encrypted or password-protected: {error_msg}")
        else:
            raise Exception(f"Failed to extract chords from PDF: {error_msg}")

    return chords, metadata


def detect_if_text_pdf(input_file_bytes: bytes, min_text_threshold: int = 50) -> bool:
    """
    Detect if a PDF is text-based (as opposed to scanned/image-based).

    Args:

        min_text_threshold: Minimum number of characters to consider it text-based

    Returns:
        True if the PDF appears to be text-based, False otherwise
    """
    # Lazy import to avoid FUNCTION_INVOCATION_FAILED in serverless environments
    try:
        import pdfplumber
    except ImportError:
        # If pdfplumber is not available, assume it's not a text PDF
        return False

    try:
        with pdfplumber.open(io.BytesIO(input_file_bytes)) as pdf:
            # Check first page
            if not pdf.pages:
                return False

            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # If we can extract meaningful text, it's text-based
            if text and len(text.strip()) >= min_text_threshold:
                return True

            return False

    except Exception:
        # If we can't extract text, assume it's not text-based
        return False


def get_font_mapping(font_name: str) -> str:
    """
    Map PDF font names to reportlab-compatible font names.

    Args:
        font_name: Font name from PDF

    Returns:
        Mapped font name compatible with reportlab
    """
    # Normalize font name (remove special characters, make lowercase for comparison)
    normalized = font_name.lower()

    # Check for partial matches
    if 'helvetica' in normalized:
        if 'bold' in normalized:
            return 'Helvetica-Bold'
        return 'Helvetica'
    elif 'times' in normalized or 'roman' in normalized:
        if 'bold' in normalized:
            return 'Times-Bold'
        return 'Times-Roman'
    elif 'courier' in normalized:
        if 'bold' in normalized:
            return 'Courier-Bold'
        return 'Courier'
    elif 'arial' in normalized:
        # Arial maps to Helvetica in PDF
        return 'Helvetica'

    # Default fallback
    return 'Helvetica'


def estimate_text_width(text: str, font_size: float, font_name: str = "Helvetica") -> float:
    """
    Estimate the width of text in PDF units.

    This is a rough approximation since exact width depends on the font metrics.

    Args:
        text: Text to measure
        font_size: Font size in points
        font_name: Font name

    Returns:
        Estimated width in PDF units (points)
    """
    # Average character width as a fraction of font size
    # These are approximate values
    char_width_ratios = {
        'Helvetica': 0.55,
        'Helvetica-Bold': 0.58,
        'Times-Roman': 0.50,
        'Courier': 0.60,  # Monospace
    }

    # Get the base font family
    base_font = font_name.split('-')[0] if '-' in font_name else font_name
    ratio = char_width_ratios.get(base_font, 0.55)

    return len(text) * font_size * ratio


def group_chords_by_proximity(chords: List[ChordAnnotation], threshold: float = 30.0) -> List[List[ChordAnnotation]]:
    """
    Group chords that appear on the same line (same vertical position).

    This helps identify chord progressions that appear together.

    Args:
        chords: List of chord annotations
        threshold: Maximum vertical distance (in PDF units) to consider chords on same line

    Returns:
        List of chord groups, where each group contains chords from the same line
    """
    if not chords:
        return []

    # Sort chords by page, then by vertical position (top), then horizontal (left)
    sorted_chords = sorted(chords, key=lambda c: (c.page_number, c.bbox[1], c.bbox[0]))

    groups = []
    current_group = [sorted_chords[0]]

    for chord in sorted_chords[1:]:
        last_chord = current_group[-1]

        # Check if on same page and similar vertical position
        same_page = chord.page_number == last_chord.page_number
        vertical_distance = abs(chord.bbox[1] - last_chord.bbox[1])

        if same_page and vertical_distance <= threshold:
            current_group.append(chord)
        else:
            groups.append(current_group)
            current_group = [chord]

    # Add the last group
    if current_group:
        groups.append(current_group)

    return groups


def filter_false_positives(chords: List[ChordAnnotation]) -> List[ChordAnnotation]:
    """
    Filter out likely false positive chord detections.

    Heuristics:
    - Remove single-letter chords that appear in sentences
    - Remove chords that are too large (likely headings)
    - Remove chords with unusual positioning

    Args:
        chords: List of chord annotations

    Returns:
        Filtered list of chord annotations
    """
    filtered = []

    for chord in chords:
        # Skip very large text (likely titles/headings)
        if chord.font_size > 24:
            continue

        # Skip very small text (likely footnotes)
        if chord.font_size < 8:
            continue

        # Single letter chords ('A', 'C', etc.) are risky
        # Keep them only if they match common chord patterns
        if len(chord.text) <= 1:
            # Could be 'A' chord or just letter 'A' in text
            # Keep it for now, but mark as potentially ambiguous
            pass

        filtered.append(chord)

    return filtered
