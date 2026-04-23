# tests/agents/test_backtest_agent.py
import pytest
from src.agents.backtest_agent import BacktestAgent

def test_sma_backtest_returns_metrics(sample_ohlcv):
    agent = BacktestAgent()
    result = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.0)
    assert "performance" in result
    assert "outperformance" in result
    assert "total_trades" in result
    assert result["performance"] > 0

def test_mean_reversion_backtest(sample_ohlcv):
    agent = BacktestAgent()
    result = agent.run(sample_ohlcv, strategy="MeanReversion",
                       bb_window=10, bb_dev=1.5, tc=0.0)
    assert "performance" in result
    assert result["total_trades"] >= 0

def test_transaction_costs_reduce_performance(sample_ohlcv):
    agent = BacktestAgent()
    r_no_tc = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.0)
    r_tc = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.001)
    assert r_no_tc["performance"] >= r_tc["performance"]

def test_optimize_sma_returns_valid_params(sample_ohlcv):
    agent = BacktestAgent()
    short, long, perf = agent.optimize_sma(
        sample_ohlcv, short_range=range(3, 8), long_range=range(10, 20), tc=0.0
    )
    assert short < long
    assert perf > 0