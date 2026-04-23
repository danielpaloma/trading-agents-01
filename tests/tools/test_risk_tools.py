# tests/tools/test_risk_tools.py
import pytest
from src.tools.risk_tools import (
    compute_stop_loss_price, compute_take_profit_price,
    compute_position_size, check_max_drawdown,
)
from src.models.signals import Direction

def test_stop_loss_long():
    price = compute_stop_loss_price(entry=1.1000, direction=Direction.LONG, sl_pct=0.005)
    assert price == pytest.approx(1.1000 * (1 - 0.005), rel=1e-5)

def test_stop_loss_short():
    price = compute_stop_loss_price(entry=1.1000, direction=Direction.SHORT, sl_pct=0.005)
    assert price == pytest.approx(1.1000 * (1 + 0.005), rel=1e-5)

def test_take_profit_long():
    price = compute_take_profit_price(entry=1.1000, direction=Direction.LONG, tp_pct=0.010)
    assert price == pytest.approx(1.1000 * (1 + 0.010), rel=1e-5)

def test_take_profit_short():
    price = compute_take_profit_price(entry=1.1000, direction=Direction.SHORT, tp_pct=0.010)
    assert price == pytest.approx(1.1000 * (1 - 0.010), rel=1e-5)

def test_position_size_long():
    size = compute_position_size(max_units=100000, direction=Direction.LONG)
    assert size == 100000

def test_position_size_short():
    size = compute_position_size(max_units=100000, direction=Direction.SHORT)
    assert size == -100000

def test_position_size_flat():
    size = compute_position_size(max_units=100000, direction=Direction.FLAT)
    assert size == 0

def test_check_max_drawdown_ok():
    result = check_max_drawdown(realized_pnl=-100, initial_capital=10000, max_dd_pct=0.02)
    assert result is True

def test_check_max_drawdown_breached():
    result = check_max_drawdown(realized_pnl=-250, initial_capital=10000, max_dd_pct=0.02)
    assert result is False