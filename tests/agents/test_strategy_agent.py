# tests/agents/test_strategy_agent.py
import pytest
from unittest.mock import patch
from src.agents.strategy_agent import StrategyAgent
from src.state import TradingSessionState

@pytest.fixture
def state_with_data(sample_ohlcv):
    from src.models.market_data import Bar
    state = TradingSessionState(symbol="EUR/USD")
    for ts, row in sample_ohlcv.iterrows():
        state.history.append(Bar(timestamp=ts, open=row.open, high=row.high,
                                 low=row.low, close=row.close, volume=row.volume))
    return state

def test_select_strategy_returns_valid_name(state_with_data):
    with patch("src.agents.strategy_agent.call_llm") as mock_llm:
        mock_llm.return_value = {"strategy": "SMA", "reason": "trending market"}
        agent = StrategyAgent(model="test-model", api_key="test")
        strategy = agent.select_strategy(state_with_data)
        assert strategy in ("SMA", "MeanReversion")

def test_select_strategy_falls_back_on_error(state_with_data):
    with patch("src.agents.strategy_agent.call_llm", side_effect=Exception("error")):
        agent = StrategyAgent(model="test-model", api_key="test")
        strategy = agent.select_strategy(state_with_data)
        assert strategy == "SMA"