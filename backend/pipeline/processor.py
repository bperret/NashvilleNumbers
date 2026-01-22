"""
Main Pipeline Processor

Orchestrates the conversion pipeline with explicit stages.
"""

import time
from pathlib import Path
from typing import Optional
from backend.app.models import (
    ConversionRequest,
    ConversionResult,
    StructuredError,
    PipelineStage,
    PDFMetadata,
    DebugOutput,
)
from backend.app.config import ENABLE_DEBUG_MODE
from backend.utils.logging import get_logger
from backend.utils.cleanup import TempFileManager

from .stages import ingest, detect, extract, identify, convert, render

logger = get_logger(__name__)


class NashvillePipeline:
    """
    Main pipeline for converting PDFs to Nashville numbers.

    Pipeline stages:
    1. Ingest: Validate and save PDF
    2. Detect: Determine if text-based or scanned
    3. Extract: Extract all text tokens with bounding boxes
    4. Identify: Identify which tokens are chords
    5. Convert: Convert chords to Nashville numbers
    6. Render: Generate output PDF with Nashville numbers
    """

    def __init__(self, temp_file_manager: TempFileManager):
        self.temp_manager = temp_file_manager

    def process(
        self,
        pdf_bytes: bytes,
        request: ConversionRequest,
    ) -> tuple[ConversionResult, Optional[Path]]:
        """
        Process a PDF through the full pipeline.

        Args:
            pdf_bytes: Raw PDF file bytes
            request: Conversion request with parameters

        Returns:
            Tuple of (ConversionResult, output_pdf_path or None)
        """
        logger.set_correlation_id(request.correlation_id)
        logger.info("Starting conversion pipeline", key=request.key, mode=request.mode)

        start_time = time.time()
        debug_output = DebugOutput(correlation_id=request.correlation_id) if ENABLE_DEBUG_MODE else None

        # Initialize result
        result = ConversionResult(
            success=False,
            correlation_id=request.correlation_id,
            key=request.key,
            mode=request.mode,
        )

        input_path: Optional[Path] = None
        output_path: Optional[Path] = None

        try:
            # Stage 1: Ingest
            stage_start = time.time()
            ingest_result = ingest.ingest_pdf(
                pdf_bytes=pdf_bytes,
                correlation_id=request.correlation_id,
                temp_manager=self.temp_manager,
            )
            logger.stage_complete("ingest", time.time() - stage_start)

            if not ingest_result.success:
                result.error = ingest_result.error
                return result, None

            input_path = ingest_result.data["path"]

            # Stage 2: Detect PDF type
            stage_start = time.time()
            detect_result = detect.detect_pdf_type(input_path)
            logger.stage_complete("detect", time.time() - stage_start,
                                  pdf_type=detect_result.data["pdf_type"] if detect_result.success else None)

            if not detect_result.success:
                result.error = detect_result.error
                return result, None

            pdf_metadata = detect_result.data["metadata"]
            result.pdf_metadata = pdf_metadata

            # Stage 3: Extract tokens
            stage_start = time.time()
            extract_result = extract.extract_tokens(input_path, pdf_metadata)
            logger.stage_complete("extract", time.time() - stage_start,
                                  tokens_found=len(extract_result.data["tokens"]) if extract_result.success else 0)

            if not extract_result.success:
                result.error = extract_result.error
                return result, None

            tokens = extract_result.data["tokens"]
            result.total_tokens_extracted = len(tokens)

            if debug_output:
                debug_output.extracted_tokens = [
                    {"text": t.text, "page": t.page_number, "bbox": t.bbox.to_tuple()}
                    for t in tokens[:50]  # Limit for performance
                ]

            # Stage 4: Identify chords
            stage_start = time.time()
            identify_result = identify.identify_chords(tokens)
            logger.stage_complete("identify", time.time() - stage_start,
                                  chords_found=len(identify_result.data["chord_tokens"]) if identify_result.success else 0)

            if not identify_result.success:
                result.error = identify_result.error
                return result, None

            chord_tokens = identify_result.data["chord_tokens"]
            result.total_chords_identified = len(chord_tokens)

            if len(chord_tokens) == 0:
                result.error = StructuredError(
                    stage=PipelineStage.IDENTIFY,
                    error_type="no_chords_found",
                    message="No chord symbols detected in PDF. Ensure the PDF contains chord symbols (C, Dm, G7, etc.) and is not encrypted.",
                    recoverable=False,
                )
                return result, None

            if debug_output:
                debug_output.identified_chords = [
                    {"chord": str(ct.chord), "page": ct.token.page_number}
                    for ct in chord_tokens[:50]
                ]

            # Stage 5: Convert to Nashville
            stage_start = time.time()
            convert_result = convert.convert_to_nashville(
                chord_tokens=chord_tokens,
                key=request.key,
                mode=request.mode.value,
            )
            logger.stage_complete("convert", time.time() - stage_start,
                                  conversions=len(convert_result.data["conversions"]) if convert_result.success else 0)

            if not convert_result.success:
                result.error = convert_result.error
                return result, None

            conversions = convert_result.data["conversions"]
            result.total_chords_converted = len(conversions)
            result.warnings = convert_result.data.get("warnings", [])

            if debug_output:
                debug_output.conversions = [
                    {"original": str(conv.chord_token.chord), "nashville": conv.nashville_number}
                    for conv in conversions[:50]
                ]

            # Stage 6: Render output
            stage_start = time.time()
            output_path = self.temp_manager.get_temp_path(request.correlation_id, "output.pdf")
            render_result = render.render_output_pdf(
                input_pdf_path=input_path,
                conversions=conversions,
                output_pdf_path=output_path,
                pdf_metadata=pdf_metadata,
            )
            logger.stage_complete("render", time.time() - stage_start)

            if not render_result.success:
                result.error = render_result.error
                return result, None

            # Success!
            result.success = True
            result.processing_time_seconds = time.time() - start_time

            logger.info(
                "Conversion pipeline completed successfully",
                tokens=result.total_tokens_extracted,
                chords=result.total_chords_identified,
                conversions=result.total_chords_converted,
                duration=result.processing_time_seconds,
            )

            return result, output_path

        except Exception as e:
            logger.error(f"Unexpected error in pipeline: {str(e)}", exception=str(e))
            result.error = StructuredError(
                stage=PipelineStage.CONVERT,  # Generic
                error_type="internal_error",
                message=f"Internal processing error: {str(e)}",
                recoverable=False,
            )
            return result, None

        finally:
            # Cleanup input file immediately (we have the output or failed)
            if input_path and input_path.exists():
                try:
                    input_path.unlink()
                except Exception:
                    pass
