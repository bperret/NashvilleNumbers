"""
Stage 5: Convert to Nashville Numbers

Convert identified chords to Nashville Number System notation.
"""

from typing import List
from backend.app.models import (
    StageResult,
    StructuredError,
    PipelineStage,
    ChordToken,
    NashvilleConversion,
)
from backend.core.nashville_converter import (
    convert_chord_to_nashville as core_convert,
    calculate_scale_degree,
)
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def convert_to_nashville(
    chord_tokens: List[ChordToken],
    key: str,
    mode: str,
) -> StageResult:
    """
    Convert chord tokens to Nashville numbers.

    Args:
        chord_tokens: List of identified chord tokens
        key: Musical key (e.g., "C", "G", "Bb")
        mode: "major" or "minor"

    Returns:
        StageResult with data={"conversions": List[NashvilleConversion], "warnings": List[str]}
    """
    logger.stage_start("convert", total_chords=len(chord_tokens), key=key, mode=mode)

    conversions: List[NashvilleConversion] = []
    warnings: List[str] = []

    try:
        for chord_token in chord_tokens:
            try:
                # Convert to Nashville number using existing logic
                nashville_number = core_convert(chord_token.chord, key, mode)

                # Check if chromatic
                degree, is_chromatic = calculate_scale_degree(
                    chord_token.chord.root,
                    key,
                    mode
                )

                conversion = NashvilleConversion(
                    chord_token=chord_token,
                    nashville_number=nashville_number,
                    is_chromatic=is_chromatic,
                )

                conversions.append(conversion)

            except Exception as e:
                # Log warning but continue processing
                warning = f"Failed to convert chord '{chord_token.chord}': {str(e)}"
                warnings.append(warning)
                logger.warning(warning, chord=str(chord_token.chord))

                # Keep original chord as fallback
                conversion = NashvilleConversion(
                    chord_token=chord_token,
                    nashville_number=str(chord_token.chord),  # Fallback to original
                    is_chromatic=True,
                )
                conversions.append(conversion)

        logger.info(
            f"Converted {len(conversions)} chords to Nashville numbers",
            successful_conversions=len(conversions),
            warnings=len(warnings),
        )

        return StageResult(
            success=True,
            stage=PipelineStage.CONVERT,
            data={"conversions": conversions, "warnings": warnings},
            metrics={
                "total_conversions": len(conversions),
                "chromatic_chords": sum(1 for c in conversions if c.is_chromatic),
                "warnings": len(warnings),
            },
        )

    except Exception as e:
        logger.stage_error("convert", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.CONVERT,
            error=StructuredError(
                stage=PipelineStage.CONVERT,
                error_type="conversion_error",
                message=f"Failed to convert chords to Nashville numbers: {str(e)}",
                recoverable=False,
            )
        )
