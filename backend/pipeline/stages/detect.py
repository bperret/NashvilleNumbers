"""
Stage 2: Detect PDF Type

Determine if PDF is text-based or scanned.
"""

from pathlib import Path
import pdfplumber
from backend.app.models import (
    StageResult,
    StructuredError,
    PipelineStage,
    PDFType,
    PDFMetadata,
)
from backend.app.config import MIN_TEXT_THRESHOLD
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def detect_pdf_type(pdf_path: Path) -> StageResult:
    """
    Detect if PDF is text-based or scanned.

    Args:
        pdf_path: Path to PDF file

    Returns:
        StageResult with data={"pdf_type": PDFType, "metadata": PDFMetadata}
    """
    logger.stage_start("detect", pdf_path=str(pdf_path))

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract metadata
            num_pages = len(pdf.pages)

            if num_pages == 0:
                return StageResult(
                    success=False,
                    stage=PipelineStage.DETECT,
                    error=StructuredError(
                        stage=PipelineStage.DETECT,
                        error_type="empty_pdf",
                        message="PDF has no pages",
                        recoverable=False,
                    )
                )

            # Get page sizes
            page_sizes = []
            for page in pdf.pages:
                page_sizes.append({
                    "width": float(page.width),
                    "height": float(page.height),
                })

            # Try to extract text from first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Determine PDF type based on text content
            if text and len(text.strip()) >= MIN_TEXT_THRESHOLD:
                pdf_type = PDFType.TEXT_BASED
                logger.info(f"Detected text-based PDF", text_length=len(text))
            else:
                pdf_type = PDFType.SCANNED
                logger.info(f"Detected scanned PDF")

        # Check if we support this PDF type
        if pdf_type == PDFType.SCANNED:
            return StageResult(
                success=False,
                stage=PipelineStage.DETECT,
                error=StructuredError(
                    stage=PipelineStage.DETECT,
                    error_type="unsupported_pdf_type",
                    message="This PDF appears to be a scanned image. Only text-based PDFs with selectable text are supported. Please use an OCR tool to convert the PDF to text first.",
                    recoverable=False,
                )
            )

        # Create metadata
        metadata = PDFMetadata(
            num_pages=num_pages,
            page_sizes=page_sizes,
            pdf_type=pdf_type,
            file_size_bytes=pdf_path.stat().st_size,
        )

        return StageResult(
            success=True,
            stage=PipelineStage.DETECT,
            data={"pdf_type": pdf_type, "metadata": metadata},
            metrics={"num_pages": num_pages},
        )

    except Exception as e:
        logger.stage_error("detect", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.DETECT,
            error=StructuredError(
                stage=PipelineStage.DETECT,
                error_type="detection_error",
                message=f"Failed to detect PDF type: {str(e)}",
                recoverable=False,
            )
        )
