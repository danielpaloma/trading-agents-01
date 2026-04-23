# tests/agents/test_execution_agent.py
import pytest
from unittest.mock import MagicMock
from src.agents.execution_agent import ExecutionAgent
from src.agents.risk_agent import RiskDecision
from src.state import TradingSessionState
from src.models.signals import Direction

@pytest.fixture
def mock_client():
    c = MagicMock()
    c.get_position.return_value = 0.0
    c.place_bracket_order.return_value = [MagicMock()]
    c.cancel_all_orders = MagicMock()
    c.ib = MagicMock()
    return c

@pytest.fixture
def state():
    s = TradingSessionState(symbol="EUR/USD")
    s.current_price = 1.1000
    s.current_position = 0.0
    return s

def test_execute_long_when_flat(mock_client, state):
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=True, quantity=100000,
                            stop_loss=1.0945, take_profit=1.1110, reason="ok")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.LONG)
    mock_client.place_bracket_order.assert_called_once()
    assert state.current_position == 100000

def test_no_action_when_not_approved(mock_client, state):
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=False, quantity=0,
                            stop_loss=None, take_profit=None, reason="drawdown")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.FLAT)
    mock_client.place_bracket_order.assert_not_called()

def test_close_position_on_flat_signal(mock_client, state):
    state.current_position = 100000
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=True, quantity=0,
                            stop_loss=None, take_profit=None, reason="flat")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.FLAT)
    mock_client.cancel_all_orders.assert_called_once()