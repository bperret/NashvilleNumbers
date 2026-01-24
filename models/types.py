from enum import Enum
from typing import List


class ValidationEnum(Enum):
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return any(value == item.value for item in cls)

    @classmethod
    def get_valid_values(cls) -> List[str]:
        return [item.value for item in cls]


class MusicKey(ValidationEnum):
    C = "C"
    C_SHARP = "C#"
    DB = "Db"
    D = "D"
    D_SHARP = "D#"
    EB = "Eb"
    E = "E"
    F = "F"
    F_SHARP = "F#"
    GB = "Gb"
    G = "G"
    G_SHARP = "G#"
    AB = "Ab"
    A = "A"
    A_SHARP = "A#"
    BB = "Bb"
    B = "B"


class MusicalMode(ValidationEnum):
    MAJOR = "major"
    MINOR = "minor"
