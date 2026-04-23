# src/agents/execution_agent.py
from __future__ import annotations
import logging
from ib_async import MarketOrder
from src.state import TradingSessionState
from src.agents.risk_agent import RiskDecision
from src.tools.ibkr_tools import IBKRClient
from src.models.signals import Direction

logger = logging.getLogger(__name__)

class ExecutionAgent:
    def __init__(self, client: IBKRClient):
        self.client = client

    def execute(
        self,
        state: TradingSessionState,
        decision: RiskDecision,
        contract,
        direction: Direction,
    ) -> None:
        if not decision.approved:
            logger.warning("Risk rejected: %s", decision.reason)
            return

        target = (
            decision.quantity if direction == Direction.LONG
            else -decision.quantity if direction == Direction.SHORT
            else 0.0
        )

        if target == state.current_position:
            return

        if target == 0 and state.current_position != 0:
            self.client.cancel_all_orders(contract)
            close_action = "SELL" if state.current_position > 0 else "BUY"
            qty = abs(state.current_position)
            self.client.ib.placeOrder(contract, MarketOrder(close_action, qty))
            state.current_position = 0.0
            logger.info("Closed position: %s %s", close_action, qty)
            return

        action = "BUY" if target > 0 else "SELL"
        qty = abs(target - state.current_position)

        if decision.stop_loss and decision.take_profit:
            self.client.place_bracket_order(
                contract, action, qty, decision.stop_loss, decision.take_profit
            )
        else:
            self.client.ib.placeOrder(contract, MarketOrder(action, qty))

        state.current_position = float(target)
        logger.info("Executed %s %s | SL=%s TP=%s",
                    action, qty, decision.stop_loss, decision.take_profit)