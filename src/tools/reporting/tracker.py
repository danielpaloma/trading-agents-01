# src/tools/reporting/tracker.py
"""Position tracking and P&L calculation."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ib_async import Fill

logger = logging.getLogger(__name__)


@dataclass
class PositionTracker:
    """Track fills and calculate realized P&L using FIFO matching."""
    fills: list[Fill] = field(default_factory=list)
    realized_pnl: float = 0.0
    total_commissions: float = 0.0

    def add_fill(self, fill: Fill) -> None:
        """Add a new fill and update realized P&L."""
        self.fills.append(fill)
        self._update_pnl(fill)

    def _update_pnl(self, new_fill: Fill) -> None:
        """Calculate realized P&L using FIFO matching for opposite sides."""
        new_side = new_fill.execution.side
        new_qty = new_fill.execution.shares
        new_price = new_fill.execution.price

        for fill in self.fills[:-1]:
            if new_qty <= 0:
                break

            existing_side = fill.execution.side
            existing_qty = fill.execution.shares
            existing_price = fill.execution.price

            if existing_side == new_side:
                continue

            matched_qty = min(new_qty, existing_qty)

            if new_side == "SLD" and existing_side == "BOT":
                trade_pnl = (new_price - existing_price) * matched_qty
            elif new_side == "BOT" and existing_side == "SLD":
                trade_pnl = (existing_price - new_price) * matched_qty
            else:
                continue

            self.realized_pnl += trade_pnl
            new_qty -= matched_qty

        if new_fill.commissionReport:
            self.total_commissions += new_fill.commissionReport.commission

    def get_stats(self) -> dict:
        """Return trading statistics."""
        buy_fills = [f for f in self.fills if f.execution.side == "BOT"]
        sell_fills = [f for f in self.fills if f.execution.side == "SLD"]

        total_bought = sum(f.execution.shares for f in buy_fills)
        total_sold = sum(f.execution.shares for f in sell_fills)
        avg_buy_price = (
            sum(f.execution.price * f.execution.shares for f in buy_fills) / total_bought
            if total_bought > 0 else 0.0
        )
        avg_sell_price = (
            sum(f.execution.price * f.execution.shares for f in sell_fills) / total_sold
            if total_sold > 0 else 0.0
        )

        return {
            "total_fills": len(self.fills),
            "realized_pnl": self.realized_pnl,
            "net_pnl": self.realized_pnl - self.total_commissions,
            "total_commissions": self.total_commissions,
            "total_bought": total_bought,
            "total_sold": total_sold,
            "avg_buy_price": avg_buy_price,
            "avg_sell_price": avg_sell_price,
        }

    def to_records(self) -> list[dict]:
        """Convert fills to dictionary records for reporting."""
        records = []

        for fill in self.fills:
            side = "BOT" if fill.execution.side == "BOT" else "SELL"
            qty = fill.execution.shares
            price = fill.execution.price
            time = fill.execution.time

            records.append({
                "time": time,
                "side": side,
                "qty": qty,
                "price": price,
            })

        return records