"""
Stage 6: Render Output PDF

Generate output PDF with Nashville numbers replacing original chords.
"""

from pathlib import Path
from typing import List
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

from backend.app.models import (
    StageResult,
    StructuredError,
    PipelineStage,
    NashvilleConversion,
    PDFMetadata,
)
from backend.core.coordinates import bbox_pdfplumber_to_reportlab, get_text_baseline_y
from backend.utils.logging import get_logger

logger = get_logger(__name__)


# Font mapping for reportlab compatibility
FONT_MAP = {
    'helvetica': 'Helvetica',
    'helvetica-bold': 'Helvetica-Bold',
    'times': 'Times-Roman',
    'times-roman': 'Times-Roman',
    'times-bold': 'Times-Bold',
    'courier': 'Courier',
    'arial': 'Helvetica',  # Arial maps to Helvetica
}


def map_font_name(font_name: str) -> str:
    """Map PDF font name to ReportLab-compatible font"""
    normalized = font_name.lower()

    # Check for exact match
    if normalized in FONT_MAP:
        return FONT_MAP[normalized]

    # Check for partial matches
    if 'helvetica' in normalized or 'arial' in normalized:
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

    # Default fallback
    return 'Helvetica'


def estimate_text_width(text: str, font_size: float, font_name: str = "Helvetica") -> float:
    """
    Estimate text width in PDF points.

    This is approximate since exact metrics require loading the font.
    """
    # Average character width as fraction of font size
    char_width_ratios = {
        'Helvetica': 0.55,
        'Helvetica-Bold': 0.58,
        'Times-Roman': 0.50,
        'Courier': 0.60,  # Monospace
    }

    base_font = font_name.split('-')[0] if '-' in font_name else font_name
    ratio = char_width_ratios.get(base_font, 0.55)

    return len(text) * font_size * ratio


def create_overlay_for_page(
    page_conversions: List[NashvilleConversion],
    page_width: float,
    page_height: float,
) -> io.BytesIO:
    """
    Create PDF overlay with Nashville numbers for one page.

    Args:
        page_conversions: Conversions for this page
        page_width: Page width in points
        page_height: Page height in points

    Returns:
        BytesIO buffer with overlay PDF
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for conversion in page_conversions:
        token = conversion.chord_token.token
        nashville = conversion.nashville_number

        # Convert bounding box to ReportLab coordinates
        bbox_rl = bbox_pdfplumber_to_reportlab(token.bbox, page_height)
        x0, y0, x1, y1 = bbox_rl

        # Draw white rectangle to cover original chord
        c.setFillColorRGB(1, 1, 1)  # White
        c.setStrokeColorRGB(1, 1, 1)

        padding = 2  # pixels
        c.rect(
            x0 - padding,
            y0 - padding,
            (x1 - x0) + 2 * padding,
            (y1 - y0) + 2 * padding,
            fill=1,
            stroke=0
        )

        # Map font name
        font_name = map_font_name(token.font_name)
        font_size = token.font_size

        # Adjust font size if Nashville number is wider than original
        original_width = x1 - x0
        nashville_width = estimate_text_width(nashville, font_size, font_name)

        if nashville_width > original_width * 1.2:
            font_size = font_size * (original_width / nashville_width) * 0.95

        # Draw Nashville number
        c.setFillColorRGB(0, 0, 0)  # Black text

        try:
            c.setFont(font_name, font_size)
        except Exception:
            # Fallback to Helvetica if font not available
            c.setFont('Helvetica', font_size)
            logger.warning(f"Font {font_name} not available, using Helvetica")

        # Calculate baseline Y position
        text_y = get_text_baseline_y(bbox_rl, font_size)

        # Draw the text
        c.drawString(x0, text_y, nashville)

    c.save()
    buffer.seek(0)
    return buffer


def render_output_pdf(
    input_pdf_path: Path,
    conversions: List[NashvilleConversion],
    output_pdf_path: Path,
    pdf_metadata: PDFMetadata,
) -> StageResult:
    """
    Render output PDF with Nashville numbers.

    Strategy:
    1. Load original PDF pages
    2. Create overlay pages with Nashville numbers
    3. Merge overlays onto original pages
    4. Write output PDF

    Args:
        input_pdf_path: Path to original PDF
        conversions: List of all conversions
        output_pdf_path: Path where output will be written
        pdf_metadata: PDF metadata

    Returns:
        StageResult with success status
    """
    logger.stage_start("render", total_conversions=len(conversions))

    try:
        # Group conversions by page
        conversions_by_page = {}
        for conversion in conversions:
            page_num = conversion.chord_token.token.page_number
            if page_num not in conversions_by_page:
                conversions_by_page[page_num] = []
            conversions_by_page[page_num].append(conversion)

        # Read original PDF
        pdf_reader = PdfReader(input_pdf_path)
        pdf_writer = PdfWriter()

        # Process each page
        for page_num in range(len(pdf_reader.pages)):
            original_page = pdf_reader.pages[page_num]

            # Get page size
            if page_num < len(pdf_metadata.page_sizes):
                page_width = pdf_metadata.page_sizes[page_num]['width']
                page_height = pdf_metadata.page_sizes[page_num]['height']
            else:
                # Fallback to letter size
                page_width, page_height = letter

            # Create overlay if there are conversions on this page
            if page_num in conversions_by_page:
                overlay_buffer = create_overlay_for_page(
                    conversions_by_page[page_num],
                    page_width,
                    page_height,
                )

                # Read overlay
                overlay_pdf = PdfReader(overlay_buffer)
                overlay_page = overlay_pdf.pages[0]

                # Merge overlay onto original page
                original_page.merge_page(overlay_page)

            # Add to output
            pdf_writer.add_page(original_page)

        # Write output PDF
        with open(output_pdf_path, 'wb') as output_file:
            pdf_writer.write(output_file)

        logger.info(f"Rendered output PDF", path=str(output_pdf_path))

        return StageResult(
            success=True,
            stage=PipelineStage.RENDER,
            data={"output_path": output_pdf_path},
            metrics={"pages_rendered": len(pdf_reader.pages)},
        )

    except Exception as e:
        logger.stage_error("render", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.RENDER,
            error=StructuredError(
                stage=PipelineStage.RENDER,
                error_type="render_error",
                message=f"Failed to render output PDF: {str(e)}",
                details={"exception": str(e)},
                recoverable=False,
            )
        )
