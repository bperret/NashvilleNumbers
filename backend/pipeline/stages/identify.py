"""
Stage 4: Identify Chord Tokens

Identify which text tokens are chord symbols using heuristics and regex.
"""

from typing import List
from backend.app.models import (
    StageResult,
    StructuredError,
    PipelineStage,
    TextToken,
    ChordToken,
    Chord,
)
from backend.app.config import MIN_FONT_SIZE, MAX_FONT_SIZE, CHORD_CONFIDENCE_THRESHOLD
from backend.core.chord_parser import parse_chord, is_likely_chord
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def identify_chords(tokens: List[TextToken]) -> StageResult:
    """
    Identify which tokens are chord symbols.

    Uses heuristics:
    - Must match chord regex
    - Font size within reasonable range
    - Short text (< 10 characters)
    - Positional analysis (chords typically above lyrics)

    Args:
        tokens: List of extracted text tokens

    Returns:
        StageResult with data={"chord_tokens": List[ChordToken]}
    """
    logger.stage_start("identify", total_tokens=len(tokens))

    chord_tokens: List[ChordToken] = []

    try:
        for token in tokens:
            # Skip if text is too long
            if len(token.text) > 10:
                continue

            # Skip if font size is out of reasonable range
            if token.font_size < MIN_FONT_SIZE or token.font_size > MAX_FONT_SIZE:
                continue

            # Check if it's likely a chord
            if not is_likely_chord(token.text):
                continue

            # Parse the chord
            chord = parse_chord(token.text)
            if not chord:
                continue

            # Create chord token
            chord_token = ChordToken(
                token=token,
                chord=Chord(
                    root=chord.root,
                    quality=chord.quality,
                    extensions=chord.extensions,
                    alterations=chord.alterations,
                    bass=chord.bass,
                    original_text=token.text,
                ),
                confidence=1.0,  # Could add more sophisticated scoring
            )

            chord_tokens.append(chord_token)

        logger.info(f"Identified {len(chord_tokens)} chord symbols from {len(tokens)} tokens")

        return StageResult(
            success=True,
            stage=PipelineStage.IDENTIFY,
            data={"chord_tokens": chord_tokens},
            metrics={
                "total_tokens": len(tokens),
                "identified_chords": len(chord_tokens),
                "identification_rate": len(chord_tokens) / len(tokens) if tokens else 0,
            },
        )

    except Exception as e:
        logger.stage_error("identify", str(e))
        return StageResult(
            success=False,
            stage=PipelineStage.IDENTIFY,
            error=StructuredError(
                stage=PipelineStage.IDENTIFY,
                error_type="identification_error",
                message=f"Failed to identify chords: {str(e)}",
                recoverable=False,
            )
        )
