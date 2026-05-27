# src/models/signals.py
from enum import Enum

from pydantic import BaseModel


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

class Signal(BaseModel):
    direction: Direction
    strategy: str
    confidence: float = 1.0
    reason: str = ""