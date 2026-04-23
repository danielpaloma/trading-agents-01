# tests/agents/test_analysis_agent.py
import pytest
from unittest.mock import patch
from src.agents.analysis_agent import AnalysisAgent
from src.state import TradingSessionState
from src.models.signals import Direction

@pytest.fixture
def state_with_data(sample_ohlcv):
    from src.models.market_data import Bar
    state = TradingSessionState(symbol="EUR/USD")
    for ts, row in sample_ohlcv.iterrows():
        state.history.append(Bar(timestamp=ts, open=row.open, high=row.high,
                                 low=row.low, close=row.close, volume=row.volume))
    state.current_price = float(sample_ohlcv["close"].iloc[-1])
    return state

def test_run_returns_long_signal(state_with_data):
    with patch("src.agents.analysis_agent.call_llm") as mock_llm:
        mock_llm.return_value = {"direction": "long", "strategy": "SMA", "reason": "test"}
        agent = AnalysisAgent(model="anthropic/claude-haiku-4-5", api_key="test")
        signal = agent.run(state_with_data, strategy="SMA", sma_short=5, sma_long=20)
        assert signal.direction == Direction.LONG

def test_run_falls_back_on_llm_error(state_with_data):
    with patch("src.agents.analysis_agent.call_llm", side_effect=Exception("LLM error")):
        agent = AnalysisAgent(model="anthropic/claude-haiku-4-5", api_key="test")
        signal = agent.run(state_with_data, strategy="SMA", sma_short=5, sma_long=20)
        assert signal.direction in (Direction.LONG, Direction.SHORT, Direction.FLAT)