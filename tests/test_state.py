# tests/test_state.py
from src.state import TradingSessionState
from src.models.signals import Signal, Direction

def test_state_default_values():
    state = TradingSessionState(symbol="EUR/USD")
    assert state.current_position == 0.0
    assert state.active_signal is None
    assert state.session_active is False

def test_state_update_signal():
    state = TradingSessionState(symbol="EUR/USD")
    sig = Signal(direction=Direction.LONG, strategy="SMA", reason="SMA crossover")
    state.active_signal = sig
    assert state.active_signal.direction == Direction.LONG
