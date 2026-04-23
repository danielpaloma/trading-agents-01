# src/tools/analysis_tools.py
import numpy as np
import pandas as pd
from src.models.signals import Signal, Direction

def compute_sma(df: pd.DataFrame, short: int = 10, long: int = 50) -> pd.DataFrame:
    out = df.copy()
    out["sma_short"] = out["close"].rolling(short).mean()
    out["sma_long"] = out["close"].rolling(long).mean()
    return out

def compute_bollinger_bands(df: pd.DataFrame, window: int = 20, dev: float = 2.0) -> pd.DataFrame:
    out = df.copy()
    out["sma"] = out["close"].rolling(window).mean()
    std = out["close"].rolling(window).std()
    out["upper"] = out["sma"] + dev * std
    out["lower"] = out["sma"] - dev * std
    out["distance"] = out["close"] - out["sma"]
    return out

def sma_signal(df: pd.DataFrame) -> Signal:
    last = df.iloc[-1]
    if pd.isna(last["sma_short"]) or pd.isna(last["sma_long"]):
        return Signal(direction=Direction.FLAT, strategy="SMA", reason="insufficient data")
    if last["sma_short"] > last["sma_long"]:
        return Signal(direction=Direction.LONG, strategy="SMA",
                      reason=f"SMA_S {last['sma_short']:.5f} > SMA_L {last['sma_long']:.5f}")
    return Signal(direction=Direction.SHORT, strategy="SMA",
                  reason=f"SMA_S {last['sma_short']:.5f} < SMA_L {last['sma_long']:.5f}")

def mean_reversion_signal(df: pd.DataFrame) -> Signal:
    last = df.iloc[-1]
    if pd.isna(last.get("upper", float("nan"))):
        return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                      reason="insufficient data")
    if last["close"] < last["lower"]:
        return Signal(direction=Direction.LONG, strategy="MeanReversion",
                      reason=f"price {last['close']:.5f} below lower band {last['lower']:.5f}")
    if last["close"] > last["upper"]:
        return Signal(direction=Direction.SHORT, strategy="MeanReversion",
                      reason=f"price {last['close']:.5f} above upper band {last['upper']:.5f}")
    prev = df.iloc[-2] if len(df) > 1 else None
    if prev is not None and (last["distance"] * prev["distance"] < 0):
        return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                      reason="price crossed SMA — closing position")
    return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                  reason="price within bands")
