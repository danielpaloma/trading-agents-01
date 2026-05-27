# tests/test_state.py
from src.models.signals import Direction, Signal
from src.state import TradingSessionState


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
