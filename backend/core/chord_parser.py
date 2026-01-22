"""
Chord Parser Module

Handles identification and parsing of chord symbols from text.
Supports standard Western music chord notation.
"""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Chord:
    """Represents a parsed chord with its components."""
    root: str  # Root note: C, D, Eb, F#, etc.
    quality: str = ""  # maj, min, m, dim, aug, sus, etc.
    extensions: str = ""  # 7, 9, 11, 13, etc.
    alterations: str = ""  # b5, #9, add9, etc.
    bass: Optional[str] = None  # Bass note for slash chords
    original: str = ""  # Original text for reference

    def __str__(self):
        """String representation of the chord."""
        chord_str = self.root + self.quality + self.extensions + self.alterations
        if self.bass:
            chord_str += f"/{self.bass}"
        return chord_str


# Comprehensive chord regex pattern
# Matches: C, Cm, Cmaj7, C7, Csus4, Cadd9, C#m7, Db, D/F#, Gmaj7#11, etc.
CHORD_PATTERN = re.compile(
    r'([A-G][b#]?)'  # Root note (required): A-G with optional flat/sharp
    r'(maj|min|m|dim|aug|Maj|Min|M|sus(?!\d))?'  # Quality (optional) - sus only if NOT followed by digit
    r'(\d{1,2})?'  # Extension (optional): 7, 9, 11, 13
    r'(b\d+|#\d+|add\d{1,2}|sus\d)?'  # Alterations (optional): b5, #9, add9, sus4, sus2
    r'(/[A-G][b#]?)?'  # Slash chord (optional): /E, /F#
    r'(?=\s|$|[,.])'  # Lookahead: must be followed by space, end, or punctuation
)


# Notes that are valid chord roots
VALID_ROOTS = {
    'A', 'A#', 'Ab', 'B', 'Bb', 'C', 'C#', 'Cb',
    'D', 'D#', 'Db', 'E', 'Eb', 'E#', 'F', 'F#', 'Fb',
    'G', 'G#', 'Gb'
}


def parse_chord(text: str) -> Optional[Chord]:
    """
    Parse a chord string into its components.

    Args:
        text: String potentially containing a chord symbol

    Returns:
        Chord object if valid chord found, None otherwise

    Examples:
        >>> parse_chord("C")
        Chord(root='C', quality='', extensions='', alterations='', bass=None)
        >>> parse_chord("Dm7")
        Chord(root='D', quality='m', extensions='7', alterations='', bass=None)
        >>> parse_chord("G/B")
        Chord(root='G', quality='', extensions='', alterations='', bass='B')
    """
    text = text.strip()
    match = CHORD_PATTERN.match(text)

    if not match:
        return None

    root = match.group(1)
    quality = match.group(2) or ""
    extensions = match.group(3) or ""
    alterations = match.group(4) or ""
    bass_part = match.group(5) or ""

    # Extract bass note (remove the '/')
    bass = bass_part[1:] if bass_part else None

    # Normalize quality (case-insensitive)
    quality = quality.lower() if quality else ""

    # Validate root note
    if root not in VALID_ROOTS:
        return None

    # Validate bass note if present
    if bass and bass not in VALID_ROOTS:
        return None

    # Additional validation: matched text should be close to original length
    # This helps avoid matching chords within longer words
    matched_text = match.group(0)
    if len(matched_text) < len(text) * 0.8:
        return None

    chord = Chord(
        root=root,
        quality=quality,
        extensions=extensions,
        alterations=alterations,
        bass=bass,
        original=text
    )

    return chord


def is_likely_chord(text: str) -> bool:
    """
    Heuristic to determine if text is likely a chord symbol.

    This helps distinguish chords from lyrics or other text.

    Args:
        text: String to evaluate

    Returns:
        True if text appears to be a chord, False otherwise

    Heuristics:
        - Matches chord regex pattern
        - Short length (< 10 characters)
        - Starts with capital letter A-G
        - Doesn't contain common non-chord words
    """
    text = text.strip()

    # Length check - chords are typically short
    if len(text) > 10 or len(text) == 0:
        return False

    # Must start with a note letter
    if not text[0] in 'ABCDEFG':
        return False

    # Common words that might start with A-G but aren't chords
    non_chord_words = {
        'Am', 'A', 'As', 'An', 'And', 'At', 'All', 'Away',
        'Be', 'But', 'By', 'Been',
        'Can', 'Come',
        'Do', 'Don', 'Down',
        'For', 'From',
        'Go', 'Get', 'Got'
    }

    # Special handling: 'A', 'Am', 'C' etc. could be chords or words
    # If it's exactly 'A' followed by space or line break, context matters
    # For MVP, we prioritize chord matching
    if text in non_chord_words and len(text) > 2:
        return False

    # Try to parse as chord
    chord = parse_chord(text)
    return chord is not None


def extract_chords_from_text(text: str) -> List[Chord]:
    """
    Extract all chords from a text string.

    Args:
        text: Text potentially containing multiple chords

    Returns:
        List of Chord objects found in the text

    Example:
        >>> extract_chords_from_text("C Am F G")
        [Chord(root='C'...), Chord(root='A', quality='m'...), ...]
    """
    words = text.split()
    chords = []

    for word in words:
        # Remove common punctuation that might be attached
        cleaned = word.strip('.,!?;:()')
        chord = parse_chord(cleaned)
        if chord and is_likely_chord(cleaned):
            chords.append(chord)

    return chords


def normalize_enharmonic(note: str, prefer_sharps: bool = True) -> str:
    """
    Normalize enharmonic equivalents.

    Args:
        note: Note to normalize (e.g., "C#" or "Db")
        prefer_sharps: If True, prefer sharp notation; otherwise prefer flats

    Returns:
        Normalized note name

    Examples:
        >>> normalize_enharmonic("Db", prefer_sharps=True)
        'C#'
        >>> normalize_enharmonic("C#", prefer_sharps=False)
        'Db'
    """
    # Enharmonic equivalents
    if prefer_sharps:
        enharmonic_map = {
            'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
            'Cb': 'B', 'Fb': 'E', 'E#': 'F', 'B#': 'C'
        }
    else:
        enharmonic_map = {
            'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb',
            'B': 'Cb', 'E': 'Fb', 'F': 'E#', 'C': 'B#'
        }

    return enharmonic_map.get(note, note)


def get_chord_info(chord: Chord) -> dict:
    """
    Get detailed information about a chord.

    Args:
        chord: Chord object

    Returns:
        Dictionary with chord analysis
    """
    return {
        'root': chord.root,
        'quality': chord.quality,
        'is_major': chord.quality in ['', 'maj', 'M', 'Maj'],
        'is_minor': chord.quality in ['m', 'min', 'Min'],
        'is_diminished': chord.quality == 'dim',
        'is_augmented': chord.quality == 'aug',
        'is_suspended': 'sus' in chord.quality or 'sus' in chord.alterations,
        'has_seventh': '7' in chord.extensions,
        'has_extension': bool(chord.extensions),
        'has_alteration': bool(chord.alterations),
        'is_slash_chord': chord.bass is not None,
        'bass_note': chord.bass,
        'display': str(chord)
    }
