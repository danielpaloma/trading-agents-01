# tests/agents/test_market_data_agent.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agents.market_data_agent import MarketDataAgent
from src.state import TradingSessionState
from src.models.market_data import Bar
from datetime import datetime, timezone

@pytest.fixture
def state():
    return TradingSessionState(symbol="EUR/USD")

@pytest.fixture
def mock_client():
    client = MagicMock()
    bar = Bar(timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
              open=1.1, high=1.11, low=1.09, close=1.105, volume=500)
    client.request_historical_bars = AsyncMock(return_value=[bar])
    return client

async def test_load_history_populates_state(state, mock_client):
    agent = MarketDataAgent(client=mock_client)
    await agent.load_history(state, contract=MagicMock(), bar_size="20 mins")
    assert len(state.history.bars) == 1
    assert state.history.bars[0].close == 1.105

def test_on_bar_update_appends_bar(state, mock_client):
    agent = MarketDataAgent(client=mock_client)
    bar = Bar(timestamp=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
              open=1.11, high=1.12, low=1.10, close=1.115, volume=300)
    agent.on_bar_update(state, bar)
    assert len(state.history.bars) == 1
    assert state.current_price == pytest.approx(1.115)