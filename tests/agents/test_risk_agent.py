# tests/agents/test_risk_agent.py
import pytest
from src.agents.risk_agent import RiskAgent, RiskDecision
from src.state import TradingSessionState
from src.models.signals import Signal, Direction

@pytest.fixture
def state():
    s = TradingSessionState(symbol="EUR/USD")
    s.current_price = 1.1000
    s.realized_pnl = 0.0
    return s

def test_approve_long_signal(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    signal = Signal(direction=Direction.LONG, strategy="SMA", reason="test")
    result = agent.evaluate(state, signal)
    assert result.approved is True
    assert result.quantity == 100000
    assert result.stop_loss == pytest.approx(1.1000 * 0.995, rel=1e-5)
    assert result.take_profit == pytest.approx(1.1000 * 1.010, rel=1e-5)

def test_reject_when_drawdown_exceeded(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    state.realized_pnl = -300.0
    signal = Signal(direction=Direction.LONG, strategy="SMA", reason="test")
    result = agent.evaluate(state, signal)
    assert result.approved is False
    assert "drawdown" in result.reason.lower()

def test_flat_signal_always_approved(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    signal = Signal(direction=Direction.FLAT, strategy="SMA", reason="no signal")
    result = agent.evaluate(state, signal)
    assert result.approved is True
    assert result.quantity == 0