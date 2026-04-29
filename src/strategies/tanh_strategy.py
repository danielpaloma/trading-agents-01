# src/strategies/tanh_strategy.py
"""Tanh Strategy - ML-inspired mean reversion and momentum fusion."""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.strategies.strategy_base import Strategy
from src.models.market_data import Bar


class TanhStrategy(Strategy):
    """
    Tanh Strategy: Combines mean reversion and momentum using tanh activation.

    Signals are bounded to [-1, 1] via tanh and combined with configurable
    weighting. Position is -1 (sell), 0 (neutral), or 1 (buy) based on
    combined signal strength relative to threshold.

    Mean Reversion: tanh(-z_score) - buy when price below mean
    Momentum: tanh(ROC) - follow price trend
    """

    def __init__(
        self,
        name: str,
        contract,
        mean_reversion_period: int = 20,
        momentum_period: int = 10,
        tanh_weight: float = 0.6,
        position_threshold: float = 0.3,
        units: int = 10,
    ):
        """
        Initialize TanhStrategy.

        Args:
            name: Strategy identifier
            contract: ib_async contract object
            mean_reversion_period: Bars for z-score mean reversion calculation
            momentum_period: Bars for momentum (ROC) calculation
            tanh_weight: Weight for mean reversion signal (0-1), momentum gets remainder
            position_threshold: Minimum |signal| to trigger position (0-1)
            units: Position size when signal triggers
        """
        super().__init__(name, contract, units)
        self.mean_reversion_period = mean_reversion_period
        self.momentum_period = momentum_period
        self.tanh_weight = tanh_weight
        self.position_threshold = position_threshold

    def calculate_position(self, bars: list[Bar]) -> int:
        """
        Calculate position using tanh-activated mean reversion + momentum.

        Returns:
            Target position: -units (sell), 0 (neutral), or +units (buy)
        """
        min_bars = max(self.mean_reversion_period, self.momentum_period) + 1
        if len(bars) < min_bars:
            return 0

        df = pd.DataFrame([b.model_dump() for b in bars]).set_index("timestamp")

        rolling_mean = df["close"].rolling(self.mean_reversion_period).mean()
        rolling_std = df["close"].rolling(self.mean_reversion_period).std()
        z_score = (df["close"] - rolling_mean) / rolling_std.replace(0, np.nan)
        mean_reversion_signal = np.tanh(-z_score)

        momentum = df["close"].pct_change(self.momentum_period)
        momentum_signal = np.tanh(momentum)

        momentum_weight = 1 - self.tanh_weight
        combined_signal = (
            self.tanh_weight * mean_reversion_signal +
            momentum_weight * momentum_signal
        )

        latest_signal = combined_signal.iloc[-1]

        if pd.isna(latest_signal) or abs(latest_signal) < self.position_threshold:
            position_direction = 0
        else:
            position_direction = int(np.sign(latest_signal))

        return position_direction * self.units