"""
Trading strategy implementations.
"""

import pandas as pd
import numpy as np
from .strategy_base import Strategy


class SMACrossoverStrategy(Strategy):
    """
    SMA Crossover Strategy: Go long when short SMA > long SMA, short otherwise.
    """

    def __init__(self, name: str, contract, sma_short: int = 50, sma_long: int = 200, units: int = 1000):
        """
        Initialize SMA Crossover strategy.

        Args:
            name: Strategy name
            contract: ib_async contract object
            sma_short: Short moving average period
            sma_long: Long moving average period
            units: Trading unit size
        """
        super().__init__(name, contract, units)
        self.sma_short = sma_short
        self.sma_long = sma_long

    def calculate_position(self, bars) -> int:
        """Calculate position based on SMA crossover."""
        df = self.df.copy()
        df["sma_s"] = df.close.rolling(self.sma_short).mean()
        df["sma_l"] = df.close.rolling(self.sma_long).mean()
        df.dropna(inplace=True)

        if len(df) == 0:
            return 0

        # Position: +1 if short SMA > long SMA, -1 otherwise
        position = np.where(df["sma_s"] > df["sma_l"], 1, -1)[-1]
        self.df = df

        return int(position * self.units)


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Strategy: Trade when price touches upper/lower bands or crosses SMA.
    Position: long when below lower band, short when above upper band, neutral at crossover.
    """

    def __init__(
        self,
        name: str,
        contract,
        sma_period: int = 20,
        num_std: float = 1.0,
        units: int = 1000,
    ):
        """
        Initialize Bollinger Bands strategy.

        Args:
            name: Strategy name
            contract: ib_async contract object
            sma_period: SMA period for bands centerline
            num_std: Number of standard deviations for bands
            units: Trading unit size
        """
        super().__init__(name, contract, units)
        self.sma_period = sma_period
        self.num_std = num_std

    def calculate_position(self, bars) -> int:
        """Calculate position based on Bollinger Bands."""
        df = self.df.copy()

        # Calculate Bollinger Bands
        df["SMA"] = df["close"].rolling(self.sma_period).mean()
        rolling_std = df["close"].rolling(self.sma_period).std()
        df["Lower"] = df["SMA"] - rolling_std * self.num_std
        df["Upper"] = df["SMA"] + rolling_std * self.num_std
        df["distance"] = df["close"] - df["SMA"]

        # Position logic:
        # - Long (+1) when price < lower band
        # - Short (-1) when price > upper band
        # - Neutral (0) when distance crosses zero (SMA crossover)
        # - Hold previous position otherwise (ffill)
        df["position"] = np.where(df["close"] < df.Lower, 1, np.nan)
        df["position"] = np.where(df["close"] > df.Upper, -1, df["position"])
        df["position"] = np.where(df.distance * df.distance.shift(1) < 0, 0, df["position"])
        df["position"] = df.position.ffill().fillna(0)

        if len(df) == 0:
            return 0

        position = int(df["position"][-1] * self.units)
        self.df = df

        return position


class ContrarianStrategy(Strategy):
    """
    Simple Contrarian Strategy: Go against recent price momentum.
    Position: -1 * sign(recent returns)
    """

    def __init__(self, name: str, contract, window: int = 1, units: int = 1000):
        """
        Initialize Contrarian strategy.

        Args:
            name: Strategy name
            contract: ib_async contract object
            window: Look-back window for returns
            units: Trading unit size
        """
        super().__init__(name, contract, units)
        self.window = window

    def calculate_position(self, bars) -> int:
        """Calculate position based on contrarian logic."""
        df = self.df.copy()
        df["returns"] = np.log(df["close"] / df["close"].shift())
        df["position"] = -np.sign(df.returns.rolling(self.window).mean())

        if len(df) == 0:
            return 0

        position = int(df["position"][-1] * self.units)
        self.df = df

        return position
