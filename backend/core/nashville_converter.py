"""
Nashville Number System Converter

Converts chord symbols to Nashville Number System notation.
Handles major and minor keys, chord qualities, and slash chords.
"""

from typing import Optional, Tuple
from backend.core.chord_parser import Chord, parse_chord


# Chromatic scale (semitones)
CHROMATIC = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Enharmonic equivalents for flats
FLAT_TO_SHARP = {
    'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
    'Cb': 'B', 'Fb': 'E', 'E#': 'F', 'B#': 'C'
}

# Major scale intervals (in semitones from root)
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # 1, 2, 3, 4, 5, 6, 7

# Natural minor scale intervals (in semitones from root)
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]  # 1, 2, b3, 4, 5, b6, b7

# Expected chord qualities in major keys (used for validation/hints)
MAJOR_KEY_QUALITIES = {
    1: '',      # I - major
    2: 'm',     # ii - minor
    3: 'm',     # iii - minor
    4: '',      # IV - major
    5: '',      # V - major
    6: 'm',     # vi - minor
    7: 'dim'    # vii° - diminished
}

# Expected chord qualities in minor keys
MINOR_KEY_QUALITIES = {
    1: 'm',     # i - minor
    2: 'dim',   # ii° - diminished
    3: '',      # III - major (relative major)
    4: 'm',     # iv - minor
    5: 'm',     # v - minor (or major in harmonic minor)
    6: '',      # VI - major
    7: ''       # VII - major
}


def normalize_note(note: str) -> str:
    """
    Normalize a note to sharp notation for consistent chromatic calculations.

    Args:
        note: Note name (e.g., "C", "Db", "F#")

    Returns:
        Normalized note name using sharps

    Examples:
        >>> normalize_note("Db")
        'C#'
        >>> normalize_note("F#")
        'F#'
    """
    return FLAT_TO_SHARP.get(note, note)


def get_chromatic_index(note: str) -> int:
    """
    Get the chromatic index (0-11) of a note.

    Args:
        note: Note name

    Returns:
        Index in chromatic scale (0-11)

    Examples:
        >>> get_chromatic_index("C")
        0
        >>> get_chromatic_index("F#")
        6
    """
    normalized = normalize_note(note)
    if normalized not in CHROMATIC:
        raise ValueError(f"Invalid note: {note}")
    return CHROMATIC.index(normalized)


def calculate_scale_degree(root: str, key: str, mode: str = "major") -> Tuple[int, bool]:
    """
    Calculate the scale degree of a chord root relative to a key.

    Args:
        root: Chord root note (e.g., "D")
        key: Key of the song (e.g., "C")
        mode: "major" or "minor"

    Returns:
        Tuple of (scale_degree, is_chromatic)
        - scale_degree: 1-7 for diatonic, adjusted for chromatics
        - is_chromatic: True if the chord is outside the key (accidental)

    Examples:
        >>> calculate_scale_degree("D", "C", "major")
        (2, False)  # D is the 2nd degree in C major
        >>> calculate_scale_degree("Eb", "C", "major")
        (3, True)   # Eb is chromatic (b3) in C major
    """
    root_index = get_chromatic_index(root)
    key_index = get_chromatic_index(key)

    # Calculate semitone distance from key
    semitone_distance = (root_index - key_index) % 12

    # Select scale intervals based on mode
    scale_intervals = MAJOR_SCALE_INTERVALS if mode == "major" else MINOR_SCALE_INTERVALS

    # Check if this semitone distance matches a diatonic scale degree
    if semitone_distance in scale_intervals:
        scale_degree = scale_intervals.index(semitone_distance) + 1
        return (scale_degree, False)

    # If not diatonic, find the closest scale degree
    # This handles chromatic chords like bII, #IV, bVII, etc.
    closest_degree = 1
    min_distance = 12

    for degree_idx, interval in enumerate(scale_intervals):
        distance = abs(semitone_distance - interval)
        if distance < min_distance:
            min_distance = distance
            closest_degree = degree_idx + 1

    return (closest_degree, True)


def format_scale_degree(
    degree: int,
    chord: Chord,
    is_chromatic: bool,
    mode: str = "major"
) -> str:
    """
    Format a scale degree as a Nashville number with proper notation.

    Args:
        degree: Scale degree (1-7)
        chord: Original chord object
        is_chromatic: Whether the chord is chromatic (outside the key)
        mode: "major" or "minor"

    Returns:
        Formatted Nashville number string

    Examples:
        >>> format_scale_degree(2, Chord(root="D", quality="m"), False, "major")
        '2m'
        >>> format_scale_degree(5, Chord(root="G"), False, "major")
        '5'
        >>> format_scale_degree(4, Chord(root="F", extensions="7"), False, "major")
        '47'
    """
    # Determine if quality should be explicitly shown
    expected_qualities = MAJOR_KEY_QUALITIES if mode == "major" else MINOR_KEY_QUALITIES
    expected_quality = expected_qualities.get(degree, '')

    # Normalize chord quality for comparison
    chord_quality = chord.quality.lower()

    # Build the Nashville number
    number = str(degree)

    # Add quality markers
    # In Nashville notation, we ALWAYS show: m (minor), dim, aug, sus
    # We show 'maj' only for major 7th chords (maj7, maj9, etc.)
    if chord_quality in ['m', 'min']:
        number += 'm'
    elif chord_quality == 'dim':
        number += 'dim'
    elif chord_quality == 'aug':
        number += 'aug'
    elif chord_quality in ['maj', 'M']:
        # Explicit major only with extensions (e.g., Imaj7)
        if chord.extensions:
            number += 'maj'
    elif 'sus' in chord_quality:
        number += chord_quality  # Include sus2, sus4, etc.

    # Add extensions (7, 9, 11, 13)
    if chord.extensions:
        number += chord.extensions

    # Add alterations (b5, #9, add9, sus4 if not in quality)
    if chord.alterations:
        # Avoid duplicate 'sus' if already in quality
        if 'sus' not in chord.alterations or 'sus' not in chord_quality:
            number += chord.alterations

    return number


def convert_chord_to_nashville(
    chord: Chord,
    key: str,
    mode: str = "major"
) -> str:
    """
    Convert a chord to Nashville Number System notation.

    Args:
        chord: Chord object to convert
        key: Key of the song
        mode: "major" or "minor"

    Returns:
        Nashville number string

    Examples:
        >>> chord = parse_chord("Dm7")
        >>> convert_chord_to_nashville(chord, "C", "major")
        '2m7'

        >>> chord = parse_chord("G/B")
        >>> convert_chord_to_nashville(chord, "C", "major")
        '5/3'

        >>> chord = parse_chord("F#m")
        >>> convert_chord_to_nashville(chord, "D", "major")
        '3m'
    """
    # Calculate scale degree for the root
    degree, is_chromatic = calculate_scale_degree(chord.root, key, mode)

    # Format the main Nashville number
    nashville_num = format_scale_degree(degree, chord, is_chromatic, mode)

    # Handle slash chords (e.g., G/B → 5/3)
    if chord.bass:
        bass_degree, bass_chromatic = calculate_scale_degree(chord.bass, key, mode)
        nashville_num += f"/{bass_degree}"

    return nashville_num


def convert_text_to_nashville(
    text: str,
    key: str,
    mode: str = "major"
) -> Optional[str]:
    """
    Convenience function to parse and convert a chord string.

    Args:
        text: Chord string (e.g., "Dm7")
        key: Key of the song
        mode: "major" or "minor"

    Returns:
        Nashville number string or None if parsing fails

    Example:
        >>> convert_text_to_nashville("Cmaj7", "C", "major")
        '1maj7'
    """
    chord = parse_chord(text)
    if not chord:
        return None
    return convert_chord_to_nashville(chord, key, mode)


def get_key_signature_preference(key: str) -> str:
    """
    Determine whether a key typically uses sharps or flats.

    This helps with enharmonic decisions when rendering.

    Args:
        key: Key name

    Returns:
        "sharps" or "flats"

    Examples:
        >>> get_key_signature_preference("G")
        'sharps'
        >>> get_key_signature_preference("F")
        'flats'
    """
    sharp_keys = {'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#'}
    flat_keys = {'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb'}

    # Check original key first (don't normalize yet)
    if key in flat_keys:
        return "flats"
    elif key in sharp_keys:
        return "sharps"

    # If not found directly, check normalized version
    normalized = normalize_note(key)
    if normalized in flat_keys:
        return "flats"
    elif normalized in sharp_keys:
        return "sharps"
    else:
        # C major / A minor default to sharps (arbitrary choice)
        return "sharps"


def validate_key(key: str) -> bool:
    """
    Validate that a key is a recognized note.

    Args:
        key: Key to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_key("C")
        True
        >>> validate_key("H")
        False
    """
    try:
        get_chromatic_index(key)
        return True
    except ValueError:
        return False


def detect_mode_from_chords(chords: list, key: str) -> str:
    """
    Attempt to detect if the song is in major or minor mode.

    This is a simple heuristic for MVP. Future versions could use ML.

    Args:
        chords: List of Chord objects
        key: The specified key

    Returns:
        "major" or "minor"

    Heuristic:
        - If the I chord is minor, likely minor mode
        - If many chords match minor key qualities, likely minor
        - Default to major
    """
    if not chords:
        return "major"

    # Check if the first chord (tonic) is minor
    first_chord = chords[0]
    if first_chord.root == key and first_chord.quality in ['m', 'min']:
        return "minor"

    # Count how many chords match expected qualities
    major_matches = 0
    minor_matches = 0

    for chord in chords:
        degree, _ = calculate_scale_degree(chord.root, key, "major")
        expected_major = MAJOR_KEY_QUALITIES.get(degree, '')
        expected_minor = MINOR_KEY_QUALITIES.get(degree, '')

        if chord.quality == expected_major:
            major_matches += 1
        if chord.quality == expected_minor:
            minor_matches += 1

    # Return the mode with more matches
    return "minor" if minor_matches > major_matches else "major"
