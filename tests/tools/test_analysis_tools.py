# tests/tools/test_analysis_tools.py
import pytest
import pandas as pd
from src.tools.analysis_tools import (
    compute_sma, compute_bollinger_bands, sma_signal, mean_reversion_signal
)
from src.models.signals import Direction

def test_compute_sma(sample_ohlcv):
    result = compute_sma(sample_ohlcv, short=5, long=20)
    assert "sma_short" in result.columns
    assert "sma_long" in result.columns
    assert result["sma_short"].iloc[-1] == pytest.approx(
        sample_ohlcv["close"].iloc[-5:].mean(), rel=1e-5
    )

def test_compute_bollinger_bands(sample_ohlcv):
    result = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    assert "sma" in result.columns
    assert "upper" in result.columns
    assert "lower" in result.columns
    last = result.iloc[-1]
    assert last["upper"] > last["sma"] > last["lower"]

def test_sma_signal_long(sample_ohlcv):
    df = compute_sma(sample_ohlcv, short=5, long=20)
    df.loc[df.index[-1], "sma_short"] = df.loc[df.index[-1], "sma_long"] + 0.001
    signal = sma_signal(df)
    assert signal.direction == Direction.LONG
    assert signal.strategy == "SMA"

def test_sma_signal_short(sample_ohlcv):
    df = compute_sma(sample_ohlcv, short=5, long=20)
    df.loc[df.index[-1], "sma_short"] = df.loc[df.index[-1], "sma_long"] - 0.001
    signal = sma_signal(df)
    assert signal.direction == Direction.SHORT

def test_mean_reversion_signal_long(sample_ohlcv):
    df = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    df.loc[df.index[-1], "close"] = df.loc[df.index[-1], "lower"] - 0.001
    signal = mean_reversion_signal(df)
    assert signal.direction == Direction.LONG
    assert signal.strategy == "MeanReversion"

def test_mean_reversion_signal_flat(sample_ohlcv):
    df = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    mid = (df.iloc[-1]["upper"] + df.iloc[-1]["lower"]) / 2
    df.loc[df.index[-1], "close"] = mid
    signal = mean_reversion_signal(df)
    assert signal.direction == Direction.FLAT
