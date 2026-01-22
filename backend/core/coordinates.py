"""
Coordinate System Utilities

Single source of truth for PDF coordinate transformations.

pdfplumber coordinates:
  - Origin: top-left corner
  - Y increases downward
  - Units: PDF points (72 DPI)

ReportLab coordinates:
  - Origin: bottom-left corner
  - Y increases upward
  - Units: PDF points (72 DPI)
"""

from backend.app.models import BoundingBox
from typing import Tuple


def pdfplumber_to_reportlab_y(y: float, page_height: float) -> float:
    """
    Convert Y coordinate from pdfplumber to ReportLab.

    Args:
        y: Y coordinate in pdfplumber space
        page_height: Height of the page in points

    Returns:
        Y coordinate in ReportLab space
    """
    return page_height - y


def bbox_pdfplumber_to_reportlab(bbox: BoundingBox, page_height: float) -> Tuple[float, float, float, float]:
    """
    Convert bounding box from pdfplumber to ReportLab coordinates.

    Args:
        bbox: Bounding box in pdfplumber coordinates (x0, y0, x1, y1)
        page_height: Height of the page in points

    Returns:
        Tuple of (x0, y0, x1, y1) in ReportLab coordinates
        where y0 is the bottom of the box and y1 is the top
    """
    # In pdfplumber: y0 is top of text, y1 is bottom
    # In ReportLab: y0 should be bottom, y1 should be top

    x0 = bbox.x0
    x1 = bbox.x1

    # Convert y coordinates
    reportlab_y0 = pdfplumber_to_reportlab_y(bbox.y1, page_height)  # Bottom of box
    reportlab_y1 = pdfplumber_to_reportlab_y(bbox.y0, page_height)  # Top of box

    return (x0, reportlab_y0, x1, reportlab_y1)


def get_text_baseline_y(bbox_reportlab: Tuple[float, float, float, float], font_size: float) -> float:
    """
    Calculate the baseline Y coordinate for drawing text in ReportLab.

    Args:
        bbox_reportlab: Bounding box in ReportLab coordinates (x0, y0, x1, y1)
        font_size: Font size in points

    Returns:
        Y coordinate for text baseline
    """
    x0, y0, x1, y1 = bbox_reportlab
    box_height = y1 - y0

    # Position text baseline slightly above the bottom of the box
    # Adjust by a fraction of font size for visual centering
    return y0 + (box_height - font_size) / 2 + font_size * 0.2
