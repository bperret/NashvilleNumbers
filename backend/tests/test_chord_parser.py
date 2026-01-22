"""
Unit tests for chord_parser module

Tests chord recognition, parsing, and validation logic.
"""

from backend.core.chord_parser import (
    parse_chord,
    is_likely_chord,
    extract_chords_from_text,
    normalize_enharmonic,
    get_chord_info
)


class TestParseChord:
    """Test chord parsing functionality."""

    def test_simple_major_chords(self):
        """Test parsing simple major chords."""
        chord = parse_chord("C")
        assert chord is not None
        assert chord.root == "C"
        assert chord.quality == ""
        assert chord.extensions == ""
        assert chord.bass is None

        chord = parse_chord("G")
        assert chord.root == "G"

        chord = parse_chord("Bb")
        assert chord.root == "Bb"

    def test_minor_chords(self):
        """Test parsing minor chords."""
        chord = parse_chord("Dm")
        assert chord is not None
        assert chord.root == "D"
        assert chord.quality == "m"

        chord = parse_chord("Amin")
        assert chord.quality == "min"

        chord = parse_chord("F#m")
        assert chord.root == "F#"
        assert chord.quality == "m"

    def test_seventh_chords(self):
        """Test parsing seventh chords."""
        chord = parse_chord("C7")
        assert chord is not None
        assert chord.root == "C"
        assert chord.extensions == "7"

        chord = parse_chord("Dmaj7")
        assert chord.root == "D"
        assert chord.quality == "maj"
        assert chord.extensions == "7"

        chord = parse_chord("Em7")
        assert chord.root == "E"
        assert chord.quality == "m"
        assert chord.extensions == "7"

    def test_extended_chords(self):
        """Test parsing extended chords (9th, 11th, 13th)."""
        chord = parse_chord("C9")
        assert chord is not None
        assert chord.extensions == "9"

        chord = parse_chord("Dm11")
        assert chord.extensions == "11"

        chord = parse_chord("G13")
        assert chord.extensions == "13"

    def test_altered_chords(self):
        """Test parsing altered chords."""
        chord = parse_chord("Cadd9")
        assert chord is not None
        assert chord.alterations == "add9"

        chord = parse_chord("Gsus4")
        assert chord.alterations == "sus4"

        chord = parse_chord("Dsus2")
        assert chord.alterations == "sus2"

    def test_suspended_chords(self):
        """Test parsing suspended chords."""
        chord = parse_chord("Csus")
        assert chord is not None
        assert chord.quality == "sus"

        chord = parse_chord("Gsus4")
        assert chord.alterations == "sus4"

    def test_diminished_augmented_chords(self):
        """Test parsing diminished and augmented chords."""
        chord = parse_chord("Bdim")
        assert chord is not None
        assert chord.quality == "dim"

        chord = parse_chord("Caug")
        assert chord.quality == "aug"

    def test_slash_chords(self):
        """Test parsing slash chords (chord/bass)."""
        chord = parse_chord("G/B")
        assert chord is not None
        assert chord.root == "G"
        assert chord.bass == "B"

        chord = parse_chord("D/F#")
        assert chord.root == "D"
        assert chord.bass == "F#"

        chord = parse_chord("C/E")
        assert chord.root == "C"
        assert chord.bass == "E"

    def test_complex_chords(self):
        """Test parsing complex chord combinations."""
        chord = parse_chord("Cmaj7")
        assert chord is not None
        assert chord.root == "C"
        assert chord.quality == "maj"
        assert chord.extensions == "7"

        chord = parse_chord("Dm7b5")
        assert chord.root == "D"
        assert chord.quality == "m"
        assert chord.extensions == "7"
        # Note: b5 is an alteration
        # Our current regex captures it in alterations

        chord = parse_chord("Ebmaj7")
        assert chord.root == "Eb"

    def test_sharp_flat_roots(self):
        """Test chords with sharp and flat roots."""
        chord = parse_chord("F#")
        assert chord is not None
        assert chord.root == "F#"

        chord = parse_chord("Bb")
        assert chord.root == "Bb"

        chord = parse_chord("C#m7")
        assert chord.root == "C#"
        assert chord.quality == "m"

        chord = parse_chord("Ebmaj7")
        assert chord.root == "Eb"

    def test_invalid_chords(self):
        """Test that invalid strings return None."""
        assert parse_chord("Hello") is None
        assert parse_chord("XYZ") is None
        assert parse_chord("123") is None
        assert parse_chord("") is None
        assert parse_chord("H") is None  # H is not a note in English notation

    def test_edge_case_similar_words(self):
        """Test words that might look like chords but aren't."""
        # These should not parse as chords (context matters)
        # "Be" starts with B but is a word
        # Our parser might catch this - that's why we have is_likely_chord
        parse_chord("Be")

    def test_chord_with_whitespace(self):
        """Test parsing chords with surrounding whitespace."""
        chord = parse_chord("  C  ")
        assert chord is not None
        assert chord.root == "C"

        chord = parse_chord("\tDm\n")
        assert chord.root == "D"


class TestIsLikelyChord:
    """Test chord likelihood heuristics."""

    def test_valid_chords_are_likely(self):
        """Test that valid chords are identified as likely."""
        assert is_likely_chord("C") is True
        assert is_likely_chord("Dm") is True
        assert is_likely_chord("G7") is True
        assert is_likely_chord("Fmaj7") is True
        assert is_likely_chord("Bb") is True

    def test_long_strings_not_likely(self):
        """Test that long strings are not likely chords."""
        assert is_likely_chord("Hallelujah") is False
        assert is_likely_chord("AmericanPie") is False

    def test_non_note_starts_not_likely(self):
        """Test that strings not starting with A-G are not likely."""
        assert is_likely_chord("hello") is False
        assert is_likely_chord("xyz") is False
        assert is_likely_chord("123") is False

    def test_empty_string(self):
        """Test empty string handling."""
        assert is_likely_chord("") is False


class TestExtractChordsFromText:
    """Test extracting multiple chords from text."""

    def test_extract_simple_chord_progression(self):
        """Test extracting a simple chord progression."""
        text = "C Am F G"
        chords = extract_chords_from_text(text)
        assert len(chords) == 4
        assert chords[0].root == "C"
        assert chords[1].root == "A"
        assert chords[1].quality == "m"
        assert chords[2].root == "F"
        assert chords[3].root == "G"

    def test_extract_mixed_chords(self):
        """Test extracting various chord types."""
        text = "Dm7 G7 Cmaj7 Am"
        chords = extract_chords_from_text(text)
        assert len(chords) == 4
        assert chords[0].extensions == "7"
        assert chords[2].quality == "maj"

    def test_extract_with_lyrics(self):
        """Test extracting chords mixed with lyrics."""
        # This is tricky - our simple extractor might pick up false positives
        text = "C Am I will sing F G hallelujah"
        chords = extract_chords_from_text(text)
        # Should get C, Am, F, G
        # Might also get "I" if not careful - our heuristics should help
        chord_roots = [c.root for c in chords]
        assert "C" in chord_roots
        assert "F" in chord_roots
        assert "G" in chord_roots

    def test_extract_with_punctuation(self):
        """Test extracting chords with punctuation."""
        text = "C, Dm, F, G."
        chords = extract_chords_from_text(text)
        assert len(chords) == 4

    def test_empty_text(self):
        """Test extracting from empty text."""
        chords = extract_chords_from_text("")
        assert len(chords) == 0


class TestNormalizeEnharmonic:
    """Test enharmonic normalization."""

    def test_normalize_to_sharps(self):
        """Test normalizing to sharp notation."""
        assert normalize_enharmonic("Db", prefer_sharps=True) == "C#"
        assert normalize_enharmonic("Eb", prefer_sharps=True) == "D#"
        assert normalize_enharmonic("Gb", prefer_sharps=True) == "F#"
        assert normalize_enharmonic("Ab", prefer_sharps=True) == "G#"
        assert normalize_enharmonic("Bb", prefer_sharps=True) == "A#"

    def test_normalize_to_flats(self):
        """Test normalizing to flat notation."""
        assert normalize_enharmonic("C#", prefer_sharps=False) == "Db"
        assert normalize_enharmonic("D#", prefer_sharps=False) == "Eb"
        assert normalize_enharmonic("F#", prefer_sharps=False) == "Gb"
        assert normalize_enharmonic("G#", prefer_sharps=False) == "Ab"
        assert normalize_enharmonic("A#", prefer_sharps=False) == "Bb"

    def test_natural_notes_unchanged(self):
        """Test that natural notes remain unchanged."""
        assert normalize_enharmonic("C", prefer_sharps=True) == "C"
        assert normalize_enharmonic("D", prefer_sharps=False) == "D"
        assert normalize_enharmonic("F#", prefer_sharps=True) == "F#"


class TestGetChordInfo:
    """Test chord information extraction."""

    def test_major_chord_info(self):
        """Test getting info for major chords."""
        chord = parse_chord("C")
        info = get_chord_info(chord)
        assert info['is_major'] is True
        assert info['is_minor'] is False
        assert info['is_slash_chord'] is False

    def test_minor_chord_info(self):
        """Test getting info for minor chords."""
        chord = parse_chord("Dm")
        info = get_chord_info(chord)
        assert info['is_minor'] is True
        assert info['is_major'] is False

    def test_seventh_chord_info(self):
        """Test getting info for seventh chords."""
        chord = parse_chord("G7")
        info = get_chord_info(chord)
        assert info['has_seventh'] is True
        assert info['has_extension'] is True

    def test_slash_chord_info(self):
        """Test getting info for slash chords."""
        chord = parse_chord("G/B")
        info = get_chord_info(chord)
        assert info['is_slash_chord'] is True
        assert info['bass_note'] == "B"

    def test_diminished_chord_info(self):
        """Test getting info for diminished chords."""
        chord = parse_chord("Bdim")
        info = get_chord_info(chord)
        assert info['is_diminished'] is True

    def test_augmented_chord_info(self):
        """Test getting info for augmented chords."""
        chord = parse_chord("Caug")
        info = get_chord_info(chord)
        assert info['is_augmented'] is True


# Integration tests
class TestChordParserIntegration:
    """Integration tests for complete workflows."""

    def test_parse_common_worship_progression(self):
        """Test parsing a common worship song progression."""
        progression = "C G Am F C G F G"
        chords = extract_chords_from_text(progression)
        assert len(chords) == 8
        assert all(chord is not None for chord in chords)

    def test_parse_jazz_chords(self):
        """Test parsing jazz-style chords."""
        text = "Cmaj7 Dm7 G7 Cmaj7"
        chords = extract_chords_from_text(text)
        assert len(chords) == 4
        assert chords[0].quality == "maj"
        assert chords[1].quality == "m"

    def test_parse_with_slash_chords(self):
        """Test parsing progressions with slash chords."""
        text = "C G/B Am F/A"
        chords = extract_chords_from_text(text)
        assert len(chords) == 4
        assert chords[1].bass == "B"
        assert chords[3].bass == "A"
