"""
Stage 1: Ingest PDF

Validate PDF, check size, save to temp storage.
"""

from pathlib import Path
from backend.app.models import StageResult, StructuredError, PipelineStage
from backend.app.config import MAX_FILE_SIZE_BYTES
from backend.utils.cleanup import TempFileManager
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def ingest_pdf(
    pdf_bytes: bytes,
    correlation_id: str,
    temp_manager: TempFileManager,
) -> StageResult:
    """
    Validate and save PDF to temp storage.

    Args:
        pdf_bytes: Raw PDF file bytes
        correlation_id: Request correlation ID
        temp_manager: Temp file manager

    Returns:
        StageResult with data={"path": Path} on success
    """
    logger.stage_start("ingest", file_size_bytes=len(pdf_bytes))

    try:
        # Check file size
        if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
            return StageResult(
                success=False,
                stage=PipelineStage.INGEST,
                error=StructuredError(
                    stage=PipelineStage.INGEST,
                    error_type="file_too_large",
                    message=f"File size ({len(pdf_bytes) / 1024 / 1024:.1f} MB) exceeds maximum allowed size ({MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB)",
                    recoverable=False,
                )
            )

        # Check if it's actually a PDF (magic bytes)
        if not pdf_bytes.startswith(b'%PDF'):
            return StageResult(
                success=False,
                stage=PipelineStage.INGEST,
                error=StructuredError(
                    stage=PipelineStage.INGEST,
                    error_type="invalid_pdf",
                    message="File is not a valid PDF (magic bytes check failed)",
                    recoverable=False,
                )
            )

        # Save to temp file
        temp_path = temp_manager.get_temp_path(correlation_id, "input.pdf")

        with open(temp_path, 'wb') as f:
            f.write(pdf_bytes)

        logger.info(f"PDF saved to temp file", path=str(temp_path))

        return StageResult(
            success=True,
            stage=PipelineStage.INGEST,
            data={"path": temp_path},
            metrics={"file_size_bytes": len(pdf_bytes)},
        )

    except Exception as e:
        logger.stage_error("ingest", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.INGEST,
            error=StructuredError(
                stage=PipelineStage.INGEST,
                error_type="ingest_error",
                message=f"Failed to ingest PDF: {str(e)}",
                recoverable=False,
            )
        )
