# src/tools/risk_tools.py
from src.models.signals import Direction

def compute_stop_loss_price(entry: float, direction: Direction, sl_pct: float) -> float:
    if direction == Direction.LONG:
        return round(entry * (1 - sl_pct), 5)
    return round(entry * (1 + sl_pct), 5)

def compute_take_profit_price(entry: float, direction: Direction, tp_pct: float) -> float:
    if direction == Direction.LONG:
        return round(entry * (1 + tp_pct), 5)
    return round(entry * (1 - tp_pct), 5)

def compute_position_size(max_units: float, direction: Direction) -> float:
    if direction == Direction.LONG:
        return max_units
    if direction == Direction.SHORT:
        return -max_units
    return 0.0

def check_max_drawdown(realized_pnl: float, initial_capital: float, max_dd_pct: float) -> bool:
    """Returns True if within acceptable drawdown, False if limit breached."""
    drawdown = abs(min(realized_pnl, 0)) / initial_capital
    return drawdown <= max_dd_pct
