# src/models/market_data.py
from __future__ import annotations
from collections import deque
from datetime import datetime
from pydantic import BaseModel
import pandas as pd

class Bar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class OHLCVHistory:
    def __init__(self, max_bars: int = 500):
        self.bars: deque[Bar] = deque(maxlen=max_bars)

    def append(self, bar: Bar) -> None:
        self.bars.append(bar)

    def to_dataframe(self) -> pd.DataFrame:
        if not self.bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        return pd.DataFrame(
            [b.model_dump() for b in self.bars]
        ).set_index("timestamp")
