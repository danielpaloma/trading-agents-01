# tests/strategies/test_tanh_strategy.py
"""Tests for TanhStrategy."""
from __future__ import annotations
import pytest
import numpy as np
from datetime import datetime, timedelta

from src.strategies.tanh_strategy import TanhStrategy
from src.models.market_data import Bar


@pytest.fixture
def mock_contract():
    """Mock contract for testing."""
    class MockContract:
        symbol = "TEST"
    return MockContract()


@pytest.fixture
def tanh_strategy(mock_contract):
    """Default TanhStrategy instance."""
    return TanhStrategy(
        name="TanhTest",
        contract=mock_contract,
        mean_reversion_period=5,
        momentum_period=3,
        tanh_weight=0.6,
        position_threshold=0.3,
        units=10,
    )


def create_bars(prices: list[float]) -> list[Bar]:
    """Create Bar objects from price list."""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    bars = []
    for i, price in enumerate(prices):
        bar = Bar(
            timestamp=base_time + timedelta(minutes=i),
            open=price,
            high=price,
            low=price,
            close=price,
            volume=1000,
        )
        bars.append(bar)
    return bars


def test_insufficient_data_returns_zero(tanh_strategy):
    """Should return 0 when not enough bars."""
    bars = create_bars([100.0, 101.0, 102.0])
    position = tanh_strategy.calculate_position(bars)
    assert position == 0


def test_strong_mean_reversion_buy_signal(tanh_strategy):
    """When price drops significantly below mean, should trigger buy."""
    prices = [100.0, 100.5, 99.5, 100.0, 100.2,
              99.8, 100.1, 99.9, 95.0, 94.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    assert position > 0, f"Expected buy position, got {position}"


def test_strong_mean_reversion_sell_signal(tanh_strategy):
    """When price spikes significantly above mean, should trigger sell."""
    prices = [100.0, 100.5, 99.5, 100.0, 100.2,
              99.8, 100.1, 99.9, 105.0, 106.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    assert position < 0, f"Expected sell position, got {position}"


def test_neutral_when_signal_below_threshold(tanh_strategy):
    """When combined signal is weak (below threshold), should return neutral."""
    prices = [100.0, 100.0, 100.0, 100.0, 100.0,
              100.0, 100.0, 100.0, 100.0, 100.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    assert position == 0, f"Expected neutral position, got {position}"


def test_momentum_signal_buy(tanh_strategy):
    """With tanh_weight=0 (pure momentum), strong uptrend should trigger buy."""
    tanh_strategy.tanh_weight = 0.0
    tanh_strategy.position_threshold = 0.02

    prices = [100.0, 101.0, 102.0, 103.0, 104.0,
              105.0, 106.0, 107.0, 108.0, 109.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    assert position > 0, f"Expected momentum buy, got {position}"


def test_position_scaled_by_units(mock_contract):
    """Position should be scaled by units parameter."""
    strategy_5 = TanhStrategy(
        name="Test5",
        contract=mock_contract,
        units=5,
        mean_reversion_period=5,
        momentum_period=3,
    )
    strategy_10 = TanhStrategy(
        name="Test10",
        contract=mock_contract,
        units=10,
        mean_reversion_period=5,
        momentum_period=3,
    )

    prices = [100.0, 100.5, 99.5, 100.0, 100.2,
              99.8, 100.1, 99.9, 95.0, 94.0]
    bars = create_bars(prices)

    pos_5 = strategy_5.calculate_position(bars)
    pos_10 = strategy_10.calculate_position(bars)

    assert abs(pos_10) == 10, f"Expected position 10, got {pos_10}"
    assert abs(pos_5) == 5, f"Expected position 5, got {pos_5}"