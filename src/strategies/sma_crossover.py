# src/strategies/sma_crossover.py
"""SMA Crossover Strategy."""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.strategies.strategy_base import Strategy
from src.models.market_data import Bar


class SMACrossoverStrategy(Strategy):
    """
    SMA Crossover Strategy: Go long when short SMA > long SMA, short otherwise.
    """

    def __init__(
        self,
        name: str,
        contract,
        sma_short: int = 50,
        sma_long: int = 200,
        units: int = 1_000,
    ):
        super().__init__(name, contract, units)
        self.sma_short = sma_short
        self.sma_long = sma_long

    def calculate_position(self, bars: list[Bar]) -> int:
        """Calculate position based on SMA crossover."""
        if len(bars) < max(self.sma_short, self.sma_long):
            return 0

        df = pd.DataFrame([b.model_dump() for b in bars]).set_index("timestamp")
        df["sma_s"] = df["close"].rolling(self.sma_short).mean()
        df["sma_l"] = df["close"].rolling(self.sma_long).mean()
        df = df.dropna()

        if len(df) == 0:
            return 0

        position = np.where(df["sma_s"] > df["sma_l"], 1, -1)[-1]
        return int(position * self.units)