# tests/agents/test_monitor_agent.py
import pytest
from datetime import datetime, timezone
from src.agents.monitor_agent import MonitorAgent, MonitorResult
from src.state import TradingSessionState

@pytest.fixture
def active_state():
    s = TradingSessionState(symbol="EUR/USD")
    s.session_active = True
    s.session_start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    s.session_end = datetime(2024, 1, 1, 17, 0, tzinfo=timezone.utc)
    s.realized_pnl = 0.0
    return s

def test_session_healthy_mid_session(active_state):
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    assert result.should_stop is False

def test_session_stops_at_end_time(active_state):
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 17, 1, tzinfo=timezone.utc))
    assert result.should_stop is True
    assert "session end" in result.reason.lower()

def test_stops_on_drawdown_breach(active_state):
    active_state.realized_pnl = -300.0
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    assert result.should_stop is True
    assert "drawdown" in result.reason.lower()