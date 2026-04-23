# src/agents/backtest_agent.py
from __future__ import annotations
import numpy as np
import pandas as pd
from src.tools.analysis_tools import compute_sma, compute_bollinger_bands

class BacktestAgent:
    """Vectorized backtester for SMA crossover and MeanReversion strategies."""

    def run(
        self,
        df: pd.DataFrame,
        strategy: str = "SMA",
        sma_short: int = 10,
        sma_long: int = 50,
        bb_window: int = 20,
        bb_dev: float = 2.0,
        tc: float = 0.0,
    ) -> dict:
        data = df.copy()
        data["returns"] = np.log(data["close"] / data["close"].shift(1))

        if strategy == "SMA":
            data = compute_sma(data, short=sma_short, long=sma_long)
            data["position"] = np.where(data["sma_short"] > data["sma_long"], 1, -1)
        else:
            data = compute_bollinger_bands(data, window=bb_window, dev=bb_dev)
            data["position"] = np.where(data["close"] < data["lower"], 1, np.nan)
            data["position"] = np.where(data["close"] > data["upper"], -1, data["position"])
            data["position"] = np.where(
                data["distance"] * data["distance"].shift(1) < 0, 0, data["position"]
            )
            data["position"] = data["position"].ffill().fillna(0)

        data.dropna(inplace=True)
        data["strategy"] = data["position"].shift(1) * data["returns"]
        data["trades"] = data["position"].diff().fillna(0).abs()
        data["strategy"] = data["strategy"] - data["trades"] * tc
        data["creturns"] = data["returns"].cumsum().apply(np.exp)
        data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)

        return {
            "performance": float(data["cstrategy"].iloc[-1]),
            "buy_and_hold": float(data["creturns"].iloc[-1]),
            "outperformance": float(data["cstrategy"].iloc[-1] - data["creturns"].iloc[-1]),
            "total_trades": int(data["trades"].sum() / 2),
        }

    def optimize_sma(
        self,
        df: pd.DataFrame,
        short_range: range,
        long_range: range,
        tc: float = 0.0,
    ) -> tuple[int, int, float]:
        best_perf, best_short, best_long = -np.inf, short_range.start, long_range.start
        for s in short_range:
            for l in long_range:
                if s >= l:
                    continue
                result = self.run(df, strategy="SMA", sma_short=s, sma_long=l, tc=tc)
                if result["performance"] > best_perf:
                    best_perf = result["performance"]
                    best_short, best_long = s, l
        return best_short, best_long, best_perf