# src/agents/monitor_agent.py
from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from src.state import TradingSessionState
from src.tools.risk_tools import check_max_drawdown
from src.models.portfolio import SessionSummary

logger = logging.getLogger(__name__)

@dataclass
class MonitorResult:
    should_stop: bool
    reason: str

class MonitorAgent:
    def __init__(self, initial_capital: float, max_drawdown_pct: float):
        self.initial_capital = initial_capital
        self.max_drawdown_pct = max_drawdown_pct

    def check(self, state: TradingSessionState, now: datetime | None = None) -> MonitorResult:
        now = now or datetime.now(tz=timezone.utc)

        if state.session_end and now >= state.session_end:
            return MonitorResult(should_stop=True, reason="session end time reached")

        if not check_max_drawdown(state.realized_pnl, self.initial_capital, self.max_drawdown_pct):
            return MonitorResult(should_stop=True,
                                 reason=f"max drawdown exceeded: pnl={state.realized_pnl:.2f}")

        if state.stop_triggered:
            return MonitorResult(should_stop=True, reason="stop-loss/take-profit event received")

        return MonitorResult(should_stop=False, reason="session healthy")

    def build_summary(self, state: TradingSessionState) -> SessionSummary:
        return SessionSummary(
            start_time=state.session_start or datetime.now(tz=timezone.utc),
            end_time=datetime.now(tz=timezone.utc),
            total_trades=len(state.fills),
            realized_pnl=state.realized_pnl,
            max_drawdown=abs(min(state.realized_pnl, 0)) / self.initial_capital,
            final_position=state.current_position,
        )

    def print_summary(self, summary: SessionSummary) -> None:
        print("\n" + "=" * 50)
        print("SESSION SUMMARY")
        print(f"  Start:          {summary.start_time}")
        print(f"  End:            {summary.end_time}")
        print(f"  Total trades:   {summary.total_trades}")
        print(f"  Realized P&L:   {summary.realized_pnl:.2f}")
        print(f"  Max drawdown:   {summary.max_drawdown:.2%}")
        print(f"  Final position: {summary.final_position}")
        print("=" * 50)