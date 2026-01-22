"""
PDF Renderer

Renders output PDFs with Nashville numbers replacing chord symbols.
Preserves original layout, fonts, and formatting as much as possible.

Note: pdf2image is imported lazily only when needed for scanned PDF rendering.
This prevents import errors in serverless environments where system dependencies
(poppler) may not be available.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
import io
from typing import List, Dict, Any
from backend.core.text_pdf_handler import ChordAnnotation, get_font_mapping, estimate_text_width


def render_text_pdf_with_nashville(
    original_pdf_path: str,
    chord_annotations: List[ChordAnnotation],
    nashville_numbers: List[str],
    output_path: str,
    metadata: Dict[str, Any]
) -> None:
    """
    Render a new PDF with Nashville numbers replacing original chords.

    Strategy:
    1. Load original PDF as background
    2. Draw white rectangles over original chord positions
    3. Draw Nashville numbers at the same positions with similar fonts

    Args:
        original_pdf_path: Path to original PDF file
        chord_annotations: List of detected chords with positions
        nashville_numbers: List of Nashville number strings (parallel to chord_annotations)
        output_path: Path where output PDF will be saved
        metadata: PDF metadata including page sizes

    Raises:
        Exception: If rendering fails
    """
    try:
        # Read original PDF
        pdf_reader = PdfReader(original_pdf_path)
        pdf_writer = PdfWriter()

        # Group chords by page
        chords_by_page: Dict[int, List[tuple]] = {}
        for annotation, nashville in zip(chord_annotations, nashville_numbers):
            page_num = annotation.page_number
            if page_num not in chords_by_page:
                chords_by_page[page_num] = []
            chords_by_page[page_num].append((annotation, nashville))

        # Process each page
        for page_num in range(len(pdf_reader.pages)):
            original_page = pdf_reader.pages[page_num]

            # Get page size
            if page_num < len(metadata['page_sizes']):
                page_width = metadata['page_sizes'][page_num]['width']
                page_height = metadata['page_sizes'][page_num]['height']
            else:
                # Fallback to letter size
                page_width, page_height = letter

            # Create overlay with Nashville numbers
            if page_num in chords_by_page:
                overlay_buffer = create_chord_overlay(
                    chords_by_page[page_num],
                    page_width,
                    page_height
                )

                # Read the overlay
                overlay_pdf = PdfReader(overlay_buffer)
                overlay_page = overlay_pdf.pages[0]

                # Merge overlay onto original page
                original_page.merge_page(overlay_page)

            # Add to output
            pdf_writer.add_page(original_page)

        # Write output PDF
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)

    except Exception as e:
        raise Exception(f"Failed to render PDF: {str(e)}")


def create_chord_overlay(
    page_chords: List[tuple],
    page_width: float,
    page_height: float
) -> io.BytesIO:
    """
    Create a transparent PDF overlay with Nashville numbers.

    Args:
        page_chords: List of (ChordAnnotation, nashville_string) tuples for this page
        page_width: Page width in points
        page_height: Page height in points

    Returns:
        BytesIO buffer containing the overlay PDF
    """
    buffer = io.BytesIO()

    # Create canvas with page size
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for annotation, nashville in page_chords:
        # Get chord position
        x0, y0, x1, y1 = annotation.bbox

        # PDF coordinates: origin at bottom-left
        # pdfplumber coordinates: origin at top-left
        # Need to convert y-coordinates
        pdf_y0 = page_height - y1  # Bottom of text box
        pdf_y1 = page_height - y0  # Top of text box

        # Draw white rectangle to cover original chord
        c.setFillColorRGB(1, 1, 1)  # White
        c.setStrokeColorRGB(1, 1, 1)  # White border

        # Add a bit of padding to ensure complete coverage
        padding = 2
        c.rect(
            x0 - padding,
            pdf_y0 - padding,
            (x1 - x0) + 2 * padding,
            (pdf_y1 - pdf_y0) + 2 * padding,
            fill=1,
            stroke=0
        )

        # Map font name to reportlab font
        font_name = get_font_mapping(annotation.font_name)
        font_size = annotation.font_size

        # Estimate if Nashville number will fit in original space
        original_width = x1 - x0
        nashville_width = estimate_text_width(nashville, font_size, font_name)

        # Adjust font size if Nashville number is significantly wider
        if nashville_width > original_width * 1.2:
            font_size = font_size * (original_width / nashville_width) * 0.95

        # Draw Nashville number
        c.setFillColorRGB(0, 0, 0)  # Black text
        try:
            c.setFont(font_name, font_size)
        except Exception:
            # Fallback to Helvetica if font not available
            c.setFont('Helvetica', font_size)

        # Center the text vertically in the original space
        text_y = pdf_y0 + (pdf_y1 - pdf_y0 - font_size) / 2 + font_size * 0.2

        # Draw the Nashville number
        c.drawString(x0, text_y, nashville)

    # Finalize the canvas
    c.save()
    buffer.seek(0)
    return buffer


def render_scanned_pdf_with_nashville(
    original_pdf_path: str,
    chord_annotations: List[ChordAnnotation],
    nashville_numbers: List[str],
    output_path: str,
    metadata: Dict[str, Any]
) -> None:
    """
    Render a scanned/image-based PDF with Nashville numbers.

    Strategy:
    1. Convert PDF pages to images
    2. Create new PDF with images as background
    3. Overlay Nashville numbers at detected positions

    Args:
        original_pdf_path: Path to original PDF file
        chord_annotations: List of detected chords with positions
        nashville_numbers: List of Nashville number strings
        output_path: Path where output PDF will be saved
        metadata: PDF metadata including page sizes

    Raises:
        Exception: If rendering fails
    """
    # Lazy import to avoid loading dependencies in serverless environments
    try:
        from pdf2image import convert_from_path
    except ImportError as e:
        raise Exception(
            "pdf2image dependency not available. This feature requires pdf2image "
            "with system dependency poppler. "
            f"Import error: {str(e)}"
        )

    try:
        # Convert PDF pages to images
        images = convert_from_path(original_pdf_path, dpi=150)

        # Group chords by page
        chords_by_page: Dict[int, List[tuple]] = {}
        for annotation, nashville in zip(chord_annotations, nashville_numbers):
            page_num = annotation.page_number
            if page_num not in chords_by_page:
                chords_by_page[page_num] = []
            chords_by_page[page_num].append((annotation, nashville))

        # Create output PDF
        c = canvas.Canvas(output_path, pagesize=letter)

        for page_num, img in enumerate(images):
            # Get page size
            if page_num < len(metadata['page_sizes']):
                page_width = metadata['page_sizes'][page_num]['width']
                page_height = metadata['page_sizes'][page_num]['height']
            else:
                page_width, page_height = letter

            c.setPageSize((page_width, page_height))

            # Draw image as background
            # Convert PIL image to ImageReader
            img_reader = ImageReader(img)
            c.drawImage(img_reader, 0, 0, width=page_width, height=page_height)

            # Draw Nashville numbers if any on this page
            if page_num in chords_by_page:
                for annotation, nashville in chords_by_page[page_num]:
                    # Get chord position
                    x0, y0, x1, y1 = annotation.bbox

                    # Convert coordinates
                    pdf_y0 = page_height - y1
                    pdf_y1 = page_height - y0

                    # Draw white rectangle to cover original chord
                    c.setFillColorRGB(1, 1, 1)
                    padding = 2
                    c.rect(
                        x0 - padding,
                        pdf_y0 - padding,
                        (x1 - x0) + 2 * padding,
                        (pdf_y1 - pdf_y0) + 2 * padding,
                        fill=1,
                        stroke=0
                    )

                    # Draw Nashville number
                    c.setFillColorRGB(0, 0, 0)
                    font_name = get_font_mapping(annotation.font_name)
                    font_size = annotation.font_size

                    try:
                        c.setFont(font_name, font_size)
                    except Exception:
                        c.setFont('Helvetica', font_size)

                    text_y = pdf_y0 + (pdf_y1 - pdf_y0 - font_size) / 2 + font_size * 0.2
                    c.drawString(x0, text_y, nashville)

            # Move to next page
            c.showPage()

        # Save the PDF
        c.save()

    except Exception as e:
        raise Exception(f"Failed to render scanned PDF: {str(e)}")


def estimate_render_quality(
    chord_annotations: List[ChordAnnotation],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Estimate the quality of the rendering based on chord detection.

    Args:
        chord_annotations: List of detected chords
        metadata: PDF metadata

    Returns:
        Dictionary with quality metrics
    """
    return {
        'total_chords': len(chord_annotations),
        'avg_font_size': sum(c.font_size for c in chord_annotations) / len(chord_annotations) if chord_annotations else 0,
        'pages_with_chords': len(set(c.page_number for c in chord_annotations)),
        'total_pages': metadata.get('num_pages', 0),
        'coverage': len(set(c.page_number for c in chord_annotations)) / max(metadata.get('num_pages', 1), 1)
    }
