# src/models/signals.py
from enum import StrEnum

from pydantic import BaseModel


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class Signal(BaseModel):
    direction: Direction
    strategy: str
    confidence: float = 1.0
    reason: str = ""
