# src/strategies/bollinger_bands.py
"""Bollinger Bands Strategy."""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.strategies.strategy_base import Strategy
from src.models.market_data import Bar


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Strategy: Trade when price touches upper/lower bands.
    Long when below lower band, short when above upper band, neutral at crossover.
    """

    def __init__(
        self,
        name: str,
        contract,
        sma_period: int = 20,
        num_std: float = 1.0,
        units: int = 1_000,
    ):
        super().__init__(name, contract, units)
        self.sma_period = sma_period
        self.num_std = num_std

    def calculate_position(self, bars: list[Bar]) -> int:
        """Calculate position based on Bollinger Bands."""
        if len(bars) < self.sma_period:
            return 0

        df = pd.DataFrame([b.model_dump() for b in bars]).set_index("timestamp")
        df["sma"] = df["close"].rolling(self.sma_period).mean()
        rolling_std = df["close"].rolling(self.sma_period).std()
        df["lower"] = df["sma"] - rolling_std * self.num_std
        df["upper"] = df["sma"] + rolling_std * self.num_std
        df["distance"] = df["close"] - df["sma"]

        df["position"] = np.where(df["close"] < df["lower"], 1, float("nan"))
        df["position"] = np.where(df["close"] > df["upper"], -1, df["position"])
        df["position"] = np.where(
            df["distance"] * df["distance"].shift(1) < 0, 0, df["position"]
        )
        df["position"] = df["position"].ffill().fillna(0)

        if len(df) == 0:
            return 0

        return int(df["position"].iloc[-1] * self.units)