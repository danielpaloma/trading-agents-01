# src/agents/risk_agent.py
from __future__ import annotations
from dataclasses import dataclass
from src.state import TradingSessionState
from src.models.signals import Signal, Direction
from src.tools.risk_tools import (
    compute_stop_loss_price, compute_take_profit_price,
    compute_position_size, check_max_drawdown,
)

@dataclass
class RiskDecision:
    approved: bool
    quantity: float
    stop_loss: float | None
    take_profit: float | None
    reason: str

class RiskAgent:
    def __init__(
        self,
        max_units: float,
        sl_pct: float,
        tp_pct: float,
        max_drawdown_pct: float,
        initial_capital: float = 10000.0,
    ):
        self.max_units = max_units
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.initial_capital = initial_capital

    def evaluate(self, state: TradingSessionState, signal: Signal) -> RiskDecision:
        if signal.direction == Direction.FLAT:
            return RiskDecision(approved=True, quantity=0, stop_loss=None,
                                take_profit=None, reason="flat signal")

        if not check_max_drawdown(state.realized_pnl, self.initial_capital, self.max_drawdown_pct):
            return RiskDecision(
                approved=False, quantity=0, stop_loss=None, take_profit=None,
                reason=f"max drawdown exceeded: pnl={state.realized_pnl:.2f}",
            )

        entry = state.current_price
        sl = compute_stop_loss_price(entry, signal.direction, self.sl_pct)
        tp = compute_take_profit_price(entry, signal.direction, self.tp_pct)
        qty = compute_position_size(self.max_units, signal.direction)

        return RiskDecision(
            approved=True, quantity=qty, stop_loss=sl, take_profit=tp,
            reason=f"approved: qty={qty}, sl={sl:.5f}, tp={tp:.5f}",
        )