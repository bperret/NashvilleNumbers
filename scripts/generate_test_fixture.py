#!/usr/bin/env python3
"""
Generate a minimal test fixture PDF for smoke testing.

This creates a simple chord chart PDF that can be used to test
the conversion pipeline.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_test_pdf(output_path: Path):
    """Generate a minimal chord chart PDF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create PDF
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Amazing Grace - Smoke Test")

    # Chord progression with lyrics
    c.setFont("Helvetica", 12)
    y_position = height - 150

    # Verse with chords above lyrics
    chord_lines = [
        ("C", "Amazing grace, how sweet the sound"),
        ("F", "That saved a wretch like me"),
        ("C", "I once was lost, but now I'm found"),
        ("G", "Was blind but now I see"),
    ]

    for chord, lyric in chord_lines:
        # Draw chord
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120, y_position, chord)

        # Draw lyric
        c.setFont("Helvetica", 11)
        c.drawString(120, y_position - 15, lyric)

        y_position -= 40

    # Add some additional chords for testing
    y_position -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(100, y_position, "Common chords: Am  Dm  G7  C/E  Fmaj7")

    # Save
    c.save()
    print(f"Generated test fixture: {output_path}")


if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "testdata" / "input.pdf"
    generate_test_pdf(output_path)
