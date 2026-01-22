#!/usr/bin/env python3
"""
Create sample test PDFs for testing the Nashville Number System converter

This script creates simple PDFs with chord progressions for testing purposes.
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

FIXTURES_DIR = Path(__file__).parent / 'fixtures' / 'input'


def create_simple_chord_chart(output_path: Path):
    """
    Create a simple PDF with a basic chord progression
    Good for testing text-based PDF extraction
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, height - 1 * inch, "Amazing Grace")

    # Artist/Key info
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, "Traditional Hymn")
    c.drawString(1 * inch, height - 1.5 * inch, "Key: G Major")

    # Chord progression - Verse
    y_pos = height - 2.5 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y_pos, "Verse:")

    y_pos -= 0.3 * inch
    c.setFont("Helvetica", 12)

    # Line 1: "Amazing grace how sweet the sound"
    chords_line1 = [
        ("G", 1 * inch),
        ("G7", 3 * inch),
        ("C", 5 * inch),
    ]

    lyrics_y = y_pos - 0.2 * inch
    c.setFont("Helvetica-Bold", 14)
    for chord, x in chords_line1:
        c.drawString(x, y_pos, chord)

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, lyrics_y, "Amazing grace how sweet the sound")

    # Line 2: "That saved a wretch like me"
    y_pos -= 0.8 * inch
    chords_line2 = [
        ("G", 1 * inch),
        ("Em", 2.5 * inch),
        ("D", 4 * inch),
        ("D7", 5.5 * inch),
    ]

    lyrics_y = y_pos - 0.2 * inch
    c.setFont("Helvetica-Bold", 14)
    for chord, x in chords_line2:
        c.drawString(x, y_pos, chord)

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, lyrics_y, "That saved a wretch like me")

    # Line 3: "I once was lost but now I'm found"
    y_pos -= 0.8 * inch
    chords_line3 = [
        ("G", 1 * inch),
        ("G7", 2.5 * inch),
        ("C", 4 * inch),
        ("G", 5.5 * inch),
    ]

    lyrics_y = y_pos - 0.2 * inch
    c.setFont("Helvetica-Bold", 14)
    for chord, x in chords_line3:
        c.drawString(x, y_pos, chord)

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, lyrics_y, "I once was lost but now I'm found")

    # Line 4: "Was blind but now I see"
    y_pos -= 0.8 * inch
    chords_line4 = [
        ("Em", 1 * inch),
        ("D", 2.5 * inch),
        ("G", 4 * inch),
    ]

    lyrics_y = y_pos - 0.2 * inch
    c.setFont("Helvetica-Bold", 14)
    for chord, x in chords_line4:
        c.drawString(x, y_pos, chord)

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, lyrics_y, "Was blind but now I see")

    # Chorus
    y_pos -= 1.2 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y_pos, "Chorus:")

    y_pos -= 0.3 * inch
    chords_chorus = [
        ("C", 1 * inch),
        ("G", 2 * inch),
        ("D", 3 * inch),
        ("Em", 4 * inch),
        ("C", 5 * inch),
        ("G", 6 * inch),
        ("D", 7 * inch),
    ]

    lyrics_y = y_pos - 0.2 * inch
    c.setFont("Helvetica-Bold", 14)
    for chord, x in chords_chorus:
        c.drawString(x, y_pos, chord)

    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, lyrics_y, "Grace, grace, God's grace")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(1 * inch, 0.5 * inch, "Generated test PDF for Nashville Number System converter")

    c.save()
    print(f"✓ Created: {output_path}")


def create_complex_chord_chart(output_path: Path):
    """
    Create a more complex PDF with various chord types
    Tests more advanced chord parsing
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1 * inch, height - 1 * inch, "Complex Chord Test Chart")

    y_pos = height - 2 * inch

    # Test different chord types
    test_chords = [
        # Basic triads
        ("Basic Major:", ["C", "D", "E", "F", "G", "A", "B"]),
        ("Basic Minor:", ["Cm", "Dm", "Em", "Fm", "Gm", "Am", "Bm"]),

        # Seventh chords
        ("Seventh Chords:", ["C7", "Cmaj7", "Cm7", "Cdim7", "C7sus4"]),

        # Extended chords
        ("Extended:", ["C9", "C11", "C13", "Cadd9"]),

        # Altered chords
        ("Altered:", ["C#", "Db", "F#m", "Bbmaj7"]),

        # Slash chords
        ("Slash Chords:", ["C/E", "G/B", "Am/C", "D/F#"]),

        # Complex
        ("Complex:", ["Cmaj9", "Dm7b5", "G7#9", "Am11"]),
    ]

    for section_name, chords in test_chords:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, y_pos, section_name)

        y_pos -= 0.3 * inch
        x_pos = 1 * inch

        c.setFont("Helvetica-Bold", 14)
        for chord in chords:
            c.drawString(x_pos, y_pos, chord)
            x_pos += 0.8 * inch

        y_pos -= 0.6 * inch

        if y_pos < 2 * inch:
            c.showPage()
            y_pos = height - 1 * inch

    c.save()
    print(f"✓ Created: {output_path}")


def create_multipage_chart(output_path: Path):
    """
    Create a multi-page PDF to test page processing
    """
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Create 3 pages
    for page_num in range(1, 4):
        c.setFont("Helvetica-Bold", 18)
        c.drawString(1 * inch, height - 1 * inch, f"Test Page {page_num}")

        y_pos = height - 2 * inch

        # Add some chords on each page
        page_chords = [
            ["C", "F", "G", "C"],
            ["Am", "Dm", "G", "C"],
            ["Em", "Am", "D", "G"],
        ]

        c.setFont("Helvetica-Bold", 14)
        for i, chord in enumerate(page_chords[page_num - 1]):
            c.drawString((1 + i * 1.5) * inch, y_pos, chord)

        y_pos -= 0.3 * inch
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, y_pos, "Line of lyrics here")

        # Footer with page number
        c.setFont("Helvetica", 10)
        c.drawString(width / 2 - 0.5 * inch, 0.5 * inch, f"Page {page_num} of 3")

        if page_num < 3:
            c.showPage()

    c.save()
    print(f"✓ Created: {output_path}")


def main():
    """Create all sample PDFs"""
    print("Creating sample test PDFs...")
    print(f"Output directory: {FIXTURES_DIR}\n")

    # Ensure directory exists
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Create different test PDFs
    create_simple_chord_chart(FIXTURES_DIR / "sample_simple.pdf")
    create_complex_chord_chart(FIXTURES_DIR / "sample_complex.pdf")
    create_multipage_chart(FIXTURES_DIR / "sample_multipage.pdf")

    print("\n✓ All sample PDFs created successfully!")
    print("\nYou can now test with:")
    print("  python test_pdf_runner.py tests/fixtures/input/sample_simple.pdf")
    print("  python test_pdf_runner.py tests/fixtures/input/sample_complex.pdf")
    print("  python test_pdf_runner.py tests/fixtures/input/sample_multipage.pdf")


if __name__ == '__main__':
    main()
