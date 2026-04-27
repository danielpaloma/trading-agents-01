# src/strategies/contrarian.py
"""Contrarian Strategy."""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.strategies.strategy_base import Strategy
from src.models.market_data import Bar


class ContrarianStrategy(Strategy):
    """
    Simple Contrarian Strategy: Go against recent price momentum.
    Position: -1 * sign(recent returns)
    """

    def __init__(self, name: str, contract, window: int = 1, units: int = 1_000):
        super().__init__(name, contract, units)
        self.window = window

    def calculate_position(self, bars: list[Bar]) -> int:
        """Calculate position based on contrarian logic."""
        if len(bars) < self.window + 1:
            return 0

        df = pd.DataFrame([b.model_dump() for b in bars]).set_index("timestamp")
        df["returns"] = np.log(df["close"] / df["close"].shift())
        df["position"] = -np.sign(df["returns"].rolling(self.window).mean())

        if len(df) == 0:
            return 0

        return int(df["position"].iloc[-1] * self.units)