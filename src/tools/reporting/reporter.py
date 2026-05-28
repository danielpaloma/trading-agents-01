# src/tools/reporting/reporter.py
"""Reporting functions for trade sessions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class _HasTradeReport(Protocol):
    def get_stats(self) -> dict[str, Any]: ...
    def to_records(self) -> list[dict[str, Any]]: ...


def log_final_report(tracker: _HasTradeReport, session_start: datetime) -> None:
    """Log the final trade report at end of session."""
    stats = tracker.get_stats()
    records = tracker.to_records()

    if not records:
        logger.info("=== FINAL TRADE REPORT ===")
        logger.info("No trades executed during this session.")
        logger.info("=== END REPORT ===")
        return

    logger.info("=" * 60)
    logger.info("FINAL TRADE REPORT - Session: %s", session_start.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)
    logger.info("SUMMARY:")
    logger.info("  Total Fills: %d", stats["total_fills"])
    logger.info("  Quantity Bought: %.0f @ avg %.5f", stats["total_bought"], stats["avg_buy_price"])
    logger.info("  Quantity Sold:   %.0f @ avg %.5f", stats["total_sold"], stats["avg_sell_price"])
    logger.info("  Gross Realized P&L: %.2f", stats["realized_pnl"])
    logger.info("  Total Commissions:  %.2f", stats["total_commissions"])
    logger.info("  Net P&L:            %.2f", stats["net_pnl"])
    logger.info("-" * 60)
    logger.info("TRADE DETAILS:")
    logger.info("  %-20s | %-6s | %8s | %10s", "Time", "Side", "Qty", "Price")
    logger.info("  " + "-" * 50)

    for r in records:
        time_str = (
            r["time"].strftime("%H:%M:%S") if isinstance(r["time"], datetime) else str(r["time"])
        )
        logger.info("  %-20s | %-6s | %8.0f | %10.5f", time_str, r["side"], r["qty"], r["price"])

    logger.info("=" * 60)
