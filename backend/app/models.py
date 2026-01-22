"""
Pydantic Models for Nashville Numbers Converter

All data structures are typed and validated.
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
from enum import Enum


class PDFType(str, Enum):
    """Type of PDF detected"""
    TEXT_BASED = "text_based"
    SCANNED = "scanned"
    UNKNOWN = "unknown"


class PipelineStage(str, Enum):
    """Pipeline processing stages"""
    INGEST = "ingest"
    DETECT = "detect"
    EXTRACT = "extract"
    IDENTIFY = "identify"
    CONVERT = "convert"
    RENDER = "render"
    CLEANUP = "cleanup"


class ConversionMode(str, Enum):
    """Musical mode"""
    MAJOR = "major"
    MINOR = "minor"


@dataclass
class BoundingBox:
    """Bounding box coordinates in PDF points (72 DPI)"""
    x0: float  # Left edge
    y0: float  # Top edge (pdfplumber coordinates)
    x1: float  # Right edge
    y1: float  # Bottom edge (pdfplumber coordinates)

    def width(self) -> float:
        return self.x1 - self.x0

    def height(self) -> float:
        return self.y1 - self.y0

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass
class TextToken:
    """A text token extracted from PDF"""
    text: str
    bbox: BoundingBox
    page_number: int  # 0-indexed
    font_name: str
    font_size: float

    def __repr__(self) -> str:
        return f"TextToken('{self.text}', page={self.page_number}, bbox=({self.bbox.x0:.1f}, {self.bbox.y0:.1f}))"


@dataclass
class Chord:
    """Parsed chord structure"""
    root: str  # e.g., "C", "F#", "Bb"
    quality: str = ""  # e.g., "m", "maj", "dim"
    extensions: str = ""  # e.g., "7", "9"
    alterations: str = ""  # e.g., "b5", "#9", "add9"
    bass: Optional[str] = None  # For slash chords
    original_text: str = ""

    def __str__(self) -> str:
        chord_str = self.root + self.quality + self.extensions + self.alterations
        if self.bass:
            chord_str += f"/{self.bass}"
        return chord_str


@dataclass
class ChordToken:
    """A chord identified in the PDF"""
    token: TextToken
    chord: Chord
    confidence: float = 1.0  # Confidence score for chord identification

    def __repr__(self) -> str:
        return f"ChordToken({self.chord}, page={self.token.page_number})"


@dataclass
class NashvilleConversion:
    """A chord converted to Nashville number"""
    chord_token: ChordToken
    nashville_number: str
    is_chromatic: bool = False  # True if outside the key

    def __repr__(self) -> str:
        return f"{self.chord_token.chord} → {self.nashville_number}"


class StructuredError(BaseModel):
    """Structured error with context"""
    stage: PipelineStage
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = False


class StageResult(BaseModel):
    """Result from a pipeline stage"""
    success: bool
    stage: PipelineStage
    data: Optional[Any] = None
    error: Optional[StructuredError] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class PDFMetadata(BaseModel):
    """Metadata about the PDF"""
    num_pages: int
    page_sizes: List[Dict[str, float]]  # [{"width": 612, "height": 792}, ...]
    pdf_type: PDFType
    file_size_bytes: int = 0


class ConversionRequest(BaseModel):
    """Request to convert a PDF"""
    correlation_id: str
    key: str
    mode: ConversionMode = ConversionMode.MAJOR

    @validator('key')
    def validate_key(cls, v):
        valid_keys = ['C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B']
        if v not in valid_keys:
            raise ValueError(f"Invalid key: {v}. Must be one of {valid_keys}")
        return v


class ConversionResult(BaseModel):
    """Result of a conversion"""
    success: bool
    correlation_id: str
    key: str
    mode: ConversionMode
    total_tokens_extracted: int = 0
    total_chords_identified: int = 0
    total_chords_converted: int = 0
    processing_time_seconds: float = 0.0
    pdf_metadata: Optional[PDFMetadata] = None
    error: Optional[StructuredError] = None
    warnings: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class DebugOutput(BaseModel):
    """Debug information for troubleshooting"""
    correlation_id: str
    extracted_tokens: List[Dict[str, Any]] = Field(default_factory=list)
    identified_chords: List[Dict[str, Any]] = Field(default_factory=list)
    conversions: List[Dict[str, Any]] = Field(default_factory=list)
    stage_metrics: Dict[str, Any] = Field(default_factory=dict)
