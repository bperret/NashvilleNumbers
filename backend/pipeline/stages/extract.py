"""
Stage 3: Extract Text Tokens

Extract all text with bounding boxes from PDF.
"""

from pathlib import Path
from typing import List
import pdfplumber
from backend.app.models import (
    StageResult,
    StructuredError,
    PipelineStage,
    TextToken,
    BoundingBox,
    PDFMetadata,
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def extract_tokens(pdf_path: Path, pdf_metadata: PDFMetadata) -> StageResult:
    """
    Extract all text tokens with bounding boxes.

    Args:
        pdf_path: Path to PDF file
        pdf_metadata: PDF metadata from detect stage

    Returns:
        StageResult with data={"tokens": List[TextToken]}
    """
    logger.stage_start("extract", pdf_path=str(pdf_path))

    tokens: List[TextToken] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract words with bounding boxes
                words = page.extract_words()

                for word in words:
                    text = word.get('text', '').strip()

                    if not text:
                        continue

                    # Create bounding box
                    bbox = BoundingBox(
                        x0=float(word['x0']),
                        y0=float(word['top']),
                        x1=float(word['x1']),
                        y1=float(word['bottom']),
                    )

                    # Extract font information
                    font_size = float(word.get('height', 12.0))
                    font_name = word.get('fontname', 'Helvetica')

                    # Create token
                    token = TextToken(
                        text=text,
                        bbox=bbox,
                        page_number=page_num,
                        font_name=font_name,
                        font_size=font_size,
                    )

                    tokens.append(token)

        logger.info(f"Extracted {len(tokens)} text tokens")

        return StageResult(
            success=True,
            stage=PipelineStage.EXTRACT,
            data={"tokens": tokens},
            metrics={"total_tokens": len(tokens)},
        )

    except Exception as e:
        logger.stage_error("extract", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.EXTRACT,
            error=StructuredError(
                stage=PipelineStage.EXTRACT,
                error_type="extraction_error",
                message=f"Failed to extract text from PDF: {str(e)}",
                details={"exception": str(e)},
                recoverable=False,
            )
        )
