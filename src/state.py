# src/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.models.market_data import OHLCVHistory
from src.models.orders import OrderFill
from src.models.signals import Signal


@dataclass
class TradingSessionState:
    symbol: str
    history: OHLCVHistory = field(default_factory=lambda: OHLCVHistory(max_bars=500))
    current_position: float = 0.0
    current_price: float = 0.0
    active_signal: Signal | None = None
    pending_order_id: int | None = None
    fills: list[OrderFill] = field(default_factory=list)
    realized_pnl: float = 0.0
    session_active: bool = False
    session_start: datetime | None = None
    session_end: datetime | None = None
    stop_triggered: bool = False
    error_count: int = 0
