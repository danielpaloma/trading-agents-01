# src/models/portfolio.py
from datetime import datetime
from pydantic import BaseModel

class Position(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

class SessionSummary(BaseModel):
    start_time: datetime
    end_time: datetime
    total_trades: int
    realized_pnl: float
    max_drawdown: float
    final_position: float