"""
Unit tests for nashville_converter module

Tests Nashville Number System conversion logic.
"""

import pytest
from backend.core.chord_parser import parse_chord, Chord
from backend.core.nashville_converter import (
    normalize_note,
    get_chromatic_index,
    calculate_scale_degree,
    format_scale_degree,
    convert_chord_to_nashville,
    convert_text_to_nashville,
    get_key_signature_preference,
    validate_key,
    detect_mode_from_chords
)


class TestNormalizeNote:
    """Test note normalization to sharp notation."""

    def test_normalize_flats_to_sharps(self):
        """Test converting flats to sharps."""
        assert normalize_note("Db") == "C#"
        assert normalize_note("Eb") == "D#"
        assert normalize_note("Gb") == "F#"
        assert normalize_note("Ab") == "G#"
        assert normalize_note("Bb") == "A#"

    def test_natural_notes_unchanged(self):
        """Test that natural notes remain unchanged."""
        assert normalize_note("C") == "C"
        assert normalize_note("D") == "D"
        assert normalize_note("E") == "E"
        assert normalize_note("F") == "F"
        assert normalize_note("G") == "G"
        assert normalize_note("A") == "A"
        assert normalize_note("B") == "B"

    def test_sharp_notes_unchanged(self):
        """Test that sharp notes remain unchanged."""
        assert normalize_note("C#") == "C#"
        assert normalize_note("F#") == "F#"


class TestGetChromaticIndex:
    """Test chromatic index calculation."""

    def test_natural_notes(self):
        """Test getting indices for natural notes."""
        assert get_chromatic_index("C") == 0
        assert get_chromatic_index("D") == 2
        assert get_chromatic_index("E") == 4
        assert get_chromatic_index("F") == 5
        assert get_chromatic_index("G") == 7
        assert get_chromatic_index("A") == 9
        assert get_chromatic_index("B") == 11

    def test_sharp_notes(self):
        """Test getting indices for sharp notes."""
        assert get_chromatic_index("C#") == 1
        assert get_chromatic_index("D#") == 3
        assert get_chromatic_index("F#") == 6
        assert get_chromatic_index("G#") == 8
        assert get_chromatic_index("A#") == 10

    def test_flat_notes(self):
        """Test getting indices for flat notes (normalized to sharps)."""
        assert get_chromatic_index("Db") == 1  # C#
        assert get_chromatic_index("Eb") == 3  # D#
        assert get_chromatic_index("Gb") == 6  # F#
        assert get_chromatic_index("Ab") == 8  # G#
        assert get_chromatic_index("Bb") == 10  # A#

    def test_invalid_note_raises_error(self):
        """Test that invalid notes raise ValueError."""
        with pytest.raises(ValueError):
            get_chromatic_index("H")
        with pytest.raises(ValueError):
            get_chromatic_index("X")


class TestCalculateScaleDegree:
    """Test scale degree calculation."""

    def test_c_major_scale_degrees(self):
        """Test calculating scale degrees in C major."""
        # C major: C D E F G A B
        assert calculate_scale_degree("C", "C", "major") == (1, False)
        assert calculate_scale_degree("D", "C", "major") == (2, False)
        assert calculate_scale_degree("E", "C", "major") == (3, False)
        assert calculate_scale_degree("F", "C", "major") == (4, False)
        assert calculate_scale_degree("G", "C", "major") == (5, False)
        assert calculate_scale_degree("A", "C", "major") == (6, False)
        assert calculate_scale_degree("B", "C", "major") == (7, False)

    def test_g_major_scale_degrees(self):
        """Test calculating scale degrees in G major."""
        # G major: G A B C D E F#
        assert calculate_scale_degree("G", "G", "major") == (1, False)
        assert calculate_scale_degree("A", "G", "major") == (2, False)
        assert calculate_scale_degree("B", "G", "major") == (3, False)
        assert calculate_scale_degree("C", "G", "major") == (4, False)
        assert calculate_scale_degree("D", "G", "major") == (5, False)
        assert calculate_scale_degree("E", "G", "major") == (6, False)
        assert calculate_scale_degree("F#", "G", "major") == (7, False)

    def test_f_major_scale_degrees(self):
        """Test calculating scale degrees in F major."""
        # F major: F G A Bb C D E
        assert calculate_scale_degree("F", "F", "major") == (1, False)
        assert calculate_scale_degree("G", "F", "major") == (2, False)
        assert calculate_scale_degree("A", "F", "major") == (3, False)
        assert calculate_scale_degree("Bb", "F", "major") == (4, False)
        assert calculate_scale_degree("C", "F", "major") == (5, False)
        assert calculate_scale_degree("D", "F", "major") == (6, False)
        assert calculate_scale_degree("E", "F", "major") == (7, False)

    def test_chromatic_chords(self):
        """Test identifying chromatic (non-diatonic) chords."""
        # C# is not in C major
        degree, is_chromatic = calculate_scale_degree("C#", "C", "major")
        assert is_chromatic is True

        # Eb is not in C major
        degree, is_chromatic = calculate_scale_degree("Eb", "C", "major")
        assert is_chromatic is True

    def test_a_minor_scale_degrees(self):
        """Test calculating scale degrees in A minor."""
        # A natural minor: A B C D E F G
        assert calculate_scale_degree("A", "A", "minor") == (1, False)
        assert calculate_scale_degree("B", "A", "minor") == (2, False)
        assert calculate_scale_degree("C", "A", "minor") == (3, False)
        assert calculate_scale_degree("D", "A", "minor") == (4, False)
        assert calculate_scale_degree("E", "A", "minor") == (5, False)
        assert calculate_scale_degree("F", "A", "minor") == (6, False)
        assert calculate_scale_degree("G", "A", "minor") == (7, False)


class TestFormatScaleDegree:
    """Test formatting scale degrees as Nashville numbers."""

    def test_major_chord_formatting(self):
        """Test formatting major chords."""
        chord = Chord(root="C", quality="", extensions="", alterations="")
        # In C major, C is I (expected major, so no quality marker)
        result = format_scale_degree(1, chord, False, "major")
        assert result == "1"

    def test_minor_chord_formatting(self):
        """Test formatting minor chords."""
        chord = Chord(root="D", quality="m", extensions="", alterations="")
        # In C major, Dm is ii (expected minor)
        result = format_scale_degree(2, chord, False, "major")
        assert result == "2m"

    def test_seventh_chord_formatting(self):
        """Test formatting seventh chords."""
        chord = Chord(root="G", quality="", extensions="7", alterations="")
        # G7 in C major is V7
        result = format_scale_degree(5, chord, False, "major")
        assert result == "57"

    def test_major_seventh_formatting(self):
        """Test formatting major seventh chords."""
        chord = Chord(root="C", quality="maj", extensions="7", alterations="")
        # Cmaj7 in C major is Imaj7
        result = format_scale_degree(1, chord, False, "major")
        assert result == "1maj7"

    def test_diminished_chord_formatting(self):
        """Test formatting diminished chords."""
        chord = Chord(root="B", quality="dim", extensions="", alterations="")
        # Bdim in C major is vii°
        result = format_scale_degree(7, chord, False, "major")
        assert result == "7dim"

    def test_sus_chord_formatting(self):
        """Test formatting suspended chords."""
        chord = Chord(root="G", quality="sus", extensions="", alterations="")
        result = format_scale_degree(5, chord, False, "major")
        assert result == "5sus"


class TestConvertChordToNashville:
    """Test complete chord to Nashville conversion."""

    def test_c_major_basic_chords(self):
        """Test basic chords in C major."""
        # I - IV - V - I progression
        assert convert_chord_to_nashville(parse_chord("C"), "C", "major") == "1"
        assert convert_chord_to_nashville(parse_chord("F"), "C", "major") == "4"
        assert convert_chord_to_nashville(parse_chord("G"), "C", "major") == "5"

    def test_c_major_minor_chords(self):
        """Test minor chords in C major."""
        assert convert_chord_to_nashville(parse_chord("Dm"), "C", "major") == "2m"
        assert convert_chord_to_nashville(parse_chord("Em"), "C", "major") == "3m"
        assert convert_chord_to_nashville(parse_chord("Am"), "C", "major") == "6m"

    def test_c_major_seventh_chords(self):
        """Test seventh chords in C major."""
        assert convert_chord_to_nashville(parse_chord("Cmaj7"), "C", "major") == "1maj7"
        assert convert_chord_to_nashville(parse_chord("Dm7"), "C", "major") == "2m7"
        assert convert_chord_to_nashville(parse_chord("G7"), "C", "major") == "57"

    def test_g_major_chords(self):
        """Test chords in G major."""
        # G major: I ii iii IV V vi vii°
        assert convert_chord_to_nashville(parse_chord("G"), "G", "major") == "1"
        assert convert_chord_to_nashville(parse_chord("Am"), "G", "major") == "2m"
        assert convert_chord_to_nashville(parse_chord("Bm"), "G", "major") == "3m"
        assert convert_chord_to_nashville(parse_chord("C"), "G", "major") == "4"
        assert convert_chord_to_nashville(parse_chord("D"), "G", "major") == "5"
        assert convert_chord_to_nashville(parse_chord("Em"), "G", "major") == "6m"

    def test_slash_chords(self):
        """Test slash chord conversion."""
        # G/B in C major = 5/7 (B is the 7th degree of C major)
        result = convert_chord_to_nashville(parse_chord("G/B"), "C", "major")
        assert result == "5/7"

        # D/F# in G major = 5/7
        result = convert_chord_to_nashville(parse_chord("D/F#"), "G", "major")
        assert result == "5/7"

        # C/E in C major = 1/3
        result = convert_chord_to_nashville(parse_chord("C/E"), "C", "major")
        assert result == "1/3"

    def test_complex_chords(self):
        """Test complex chord conversions."""
        # Fmaj7 in C major = 4maj7
        assert convert_chord_to_nashville(parse_chord("Fmaj7"), "C", "major") == "4maj7"

        # Em7 in C major = 3m7
        assert convert_chord_to_nashville(parse_chord("Em7"), "C", "major") == "3m7"

        # Bdim in C major = 7dim
        assert convert_chord_to_nashville(parse_chord("Bdim"), "C", "major") == "7dim"

    def test_sus_chords(self):
        """Test suspended chord conversion."""
        # Gsus4 in C major = 5sus4
        chord = parse_chord("Gsus4")
        result = convert_chord_to_nashville(chord, "C", "major")
        assert "5" in result
        assert "sus" in result

    def test_flat_keys(self):
        """Test conversions in flat keys."""
        # F major: F G A Bb C D E
        assert convert_chord_to_nashville(parse_chord("F"), "F", "major") == "1"
        assert convert_chord_to_nashville(parse_chord("Gm"), "F", "major") == "2m"
        assert convert_chord_to_nashville(parse_chord("Am"), "F", "major") == "3m"
        assert convert_chord_to_nashville(parse_chord("Bb"), "F", "major") == "4"
        assert convert_chord_to_nashville(parse_chord("C"), "F", "major") == "5"

    def test_sharp_keys(self):
        """Test conversions in sharp keys."""
        # D major: D E F# G A B C#
        assert convert_chord_to_nashville(parse_chord("D"), "D", "major") == "1"
        assert convert_chord_to_nashville(parse_chord("Em"), "D", "major") == "2m"
        assert convert_chord_to_nashville(parse_chord("F#m"), "D", "major") == "3m"
        assert convert_chord_to_nashville(parse_chord("G"), "D", "major") == "4"
        assert convert_chord_to_nashville(parse_chord("A"), "D", "major") == "5"

    def test_enharmonic_equivalents(self):
        """Test that enharmonic equivalents produce same result."""
        # C# and Db should give same scale degree in a given key
        result_sharp = convert_chord_to_nashville(parse_chord("C#"), "C", "major")
        result_flat = convert_chord_to_nashville(parse_chord("Db"), "C", "major")
        # Both are chromatic and should map to same degree
        assert result_sharp == result_flat


class TestConvertTextToNashville:
    """Test convenience text conversion function."""

    def test_convert_simple_chords(self):
        """Test converting simple chord strings."""
        assert convert_text_to_nashville("C", "C", "major") == "1"
        assert convert_text_to_nashville("Dm", "C", "major") == "2m"
        assert convert_text_to_nashville("G7", "C", "major") == "57"

    def test_convert_invalid_chord(self):
        """Test that invalid chords return None."""
        assert convert_text_to_nashville("XYZ", "C", "major") is None
        assert convert_text_to_nashville("", "C", "major") is None


class TestGetKeySignaturePreference:
    """Test key signature preferences (sharps vs flats)."""

    def test_sharp_keys(self):
        """Test keys that use sharps."""
        assert get_key_signature_preference("G") == "sharps"
        assert get_key_signature_preference("D") == "sharps"
        assert get_key_signature_preference("A") == "sharps"
        assert get_key_signature_preference("E") == "sharps"

    def test_flat_keys(self):
        """Test keys that use flats."""
        assert get_key_signature_preference("F") == "flats"
        assert get_key_signature_preference("Bb") == "flats"
        assert get_key_signature_preference("Eb") == "flats"
        assert get_key_signature_preference("Ab") == "flats"

    def test_c_key_default(self):
        """Test that C defaults to sharps."""
        assert get_key_signature_preference("C") == "sharps"


class TestValidateKey:
    """Test key validation."""

    def test_valid_natural_keys(self):
        """Test that natural note keys are valid."""
        assert validate_key("C") is True
        assert validate_key("D") is True
        assert validate_key("E") is True
        assert validate_key("F") is True
        assert validate_key("G") is True
        assert validate_key("A") is True
        assert validate_key("B") is True

    def test_valid_sharp_keys(self):
        """Test that sharp keys are valid."""
        assert validate_key("C#") is True
        assert validate_key("F#") is True
        assert validate_key("G#") is True

    def test_valid_flat_keys(self):
        """Test that flat keys are valid."""
        assert validate_key("Bb") is True
        assert validate_key("Eb") is True
        assert validate_key("Ab") is True

    def test_invalid_keys(self):
        """Test that invalid keys are rejected."""
        assert validate_key("H") is False
        assert validate_key("X") is False
        assert validate_key("Z") is False


class TestDetectModeFromChords:
    """Test mode detection heuristics."""

    def test_detect_major_mode(self):
        """Test detecting major mode."""
        chords = [
            parse_chord("C"),
            parse_chord("F"),
            parse_chord("G"),
            parse_chord("Am")
        ]
        mode = detect_mode_from_chords(chords, "C")
        assert mode == "major"

    def test_detect_minor_mode_from_first_chord(self):
        """Test detecting minor mode when first chord is minor."""
        chords = [
            parse_chord("Am"),
            parse_chord("Dm"),
            parse_chord("E"),
            parse_chord("Am")
        ]
        mode = detect_mode_from_chords(chords, "A")
        assert mode == "minor"

    def test_empty_chord_list_defaults_major(self):
        """Test that empty chord list defaults to major."""
        mode = detect_mode_from_chords([], "C")
        assert mode == "major"


# Integration tests
class TestNashvilleConverterIntegration:
    """Integration tests for complete conversion workflows."""

    def test_common_worship_progression_c_major(self):
        """Test converting common worship progression in C major."""
        # C - G - Am - F (I - V - vi - IV)
        progression = ["C", "G", "Am", "F"]
        expected = ["1", "5", "6m", "4"]

        for i, chord_text in enumerate(progression):
            result = convert_text_to_nashville(chord_text, "C", "major")
            assert result == expected[i], f"Expected {expected[i]}, got {result} for {chord_text}"

    def test_common_worship_progression_g_major(self):
        """Test converting progression in G major."""
        # G - D - Em - C (I - V - vi - IV)
        progression = ["G", "D", "Em", "C"]
        expected = ["1", "5", "6m", "4"]

        for i, chord_text in enumerate(progression):
            result = convert_text_to_nashville(chord_text, "G", "major")
            assert result == expected[i]

    def test_jazz_progression(self):
        """Test converting a jazz progression."""
        # ii - V - I in C major: Dm7 - G7 - Cmaj7
        progression = ["Dm7", "G7", "Cmaj7"]
        expected = ["2m7", "57", "1maj7"]

        for i, chord_text in enumerate(progression):
            result = convert_text_to_nashville(chord_text, "C", "major")
            assert result == expected[i]

    def test_progression_with_slash_chords(self):
        """Test converting progression with slash chords."""
        # C - G/B - Am - F/A in C major
        progression = ["C", "G/B", "Am", "F/A"]
        results = [convert_text_to_nashville(c, "C", "major") for c in progression]

        assert results[0] == "1"
        assert results[1] == "5/7"  # G/B
        assert results[2] == "6m"
        assert results[3] == "4/6"  # F/A

    def test_twelve_bar_blues_in_a(self):
        """Test converting 12-bar blues progression in A."""
        # Simplified: A7 - D7 - A7 - E7
        progression = ["A7", "D7", "A7", "E7"]
        results = [convert_text_to_nashville(c, "A", "major") for c in progression]

        assert results[0] == "17"  # I7
        assert results[1] == "47"  # IV7
        assert results[2] == "17"  # I7
        assert results[3] == "57"  # V7
