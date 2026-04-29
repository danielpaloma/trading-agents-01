# Tanh Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a hybrid ML-inspired trading strategy using tanh activation to combine mean reversion and momentum signals, outputting discrete positions: -1 (sell), 0 (neutral), or 1 (buy).

**Architecture:** The TanhStrategy combines z-score based mean reversion with return-based momentum signals. Each signal is passed through a tanh activation function to bound values between -1 and 1, then combined with configurable weights. A threshold parameter determines when the combined signal triggers a position change.

**Tech Stack:** Python 3.12+, pandas, numpy, PyYAML, existing strategy framework

---

## File Structure

| File | Purpose |
|------|---------|
| `src/strategies/tanh_strategy.py` | New strategy implementation with mean reversion + momentum using tanh activation |
| `config/strategies/tanh_strategy.yaml` | Default parameters for the strategy |
| `tests/strategies/test_tanh_strategy.py` | Unit tests for signal calculation and position outputs |
| `src/strategies/factory.py` | Register TanhStrategy in the strategy factory |
| `src/strategies/__init__.py` | Export TanhStrategy from the module |

---

## Task 1: Create Tanh Strategy Implementation

**Files:**
- Create: `src/strategies/tanh_strategy.py`

### Signal Formula

The strategy computes two normalized signals:

1. **Mean Reversion Signal**: `tanh(-z_score)`
   - Compute z-score of price: `(price - mean) / std`
   - Negative because we want to buy when price is below mean (negative z-score)
   - Period: `mean_reversion_period` bars

2. **Momentum Signal**: `tanh(momentum)`
   - Compute momentum as ROC: `(price - price[N]) / price[N]`
   - Period: `momentum_period` bars
   - Can be weighted by `momentum_weight`

3. **Combined Signal**:
   ```
   combined = tanh_weight * tanh(-z_score) + (1 - tanh_weight) * tanh(momentum)
   position = sign(combined) if |combined| >= position_threshold else 0
   ```

### Strategy Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mean_reversion_period` | int | 20 | Lookback for z-score calculation |
| `momentum_period` | int | 10 | Lookback for momentum (ROC) calculation |
| `tanh_weight` | float | 0.6 | Weight for mean reversion (0-1), momentum gets (1-weight) |
| `position_threshold` | float | 0.3 | Minimum |signal| to trigger position (0-1) |
| `units` | int | 10 | Position size when signal triggers |

- [ ] **Step 1: Create the TanhStrategy class**

Create `src/strategies/tanh_strategy.py`:

```python
# src/strategies/tanh_strategy.py
"""Tanh Strategy - ML-inspired mean reversion and momentum fusion."""
from __future__ import annotations
import pandas as pd
import numpy as np
from src.strategies.strategy_base import Strategy
from src.models.market_data import Bar


class TanhStrategy(Strategy):
    """
    Tanh Strategy: Combines mean reversion and momentum using tanh activation.

    Signals are bounded to [-1, 1] via tanh and combined with configurable
    weighting. Position is -1 (sell), 0 (neutral), or 1 (buy) based on
    combined signal strength relative to threshold.

    Mean Reversion: tanh(-z_score) - buy when price below mean
    Momentum: tanh(ROC) - follow price trend
    """

    def __init__(
        self,
        name: str,
        contract,
        mean_reversion_period: int = 20,
        momentum_period: int = 10,
        tanh_weight: float = 0.6,
        position_threshold: float = 0.3,
        units: int = 10,
    ):
        """
        Initialize TanhStrategy.

        Args:
            name: Strategy identifier
            contract: ib_async contract object
            mean_reversion_period: Bars for z-score mean reversion calculation
            momentum_period: Bars for momentum (ROC) calculation
            tanh_weight: Weight for mean reversion signal (0-1), momentum gets remainder
            position_threshold: Minimum |signal| to trigger position (0-1)
            units: Position size when signal triggers
        """
        super().__init__(name, contract, units)
        self.mean_reversion_period = mean_reversion_period
        self.momentum_period = momentum_period
        self.tanh_weight = tanh_weight
        self.position_threshold = position_threshold

    def calculate_position(self, bars: list[Bar]) -> int:
        """
        Calculate position using tanh-activated mean reversion + momentum.

        Returns:
            Target position: -units (sell), 0 (neutral), or +units (buy)
        """
        min_bars = max(self.mean_reversion_period, self.momentum_period) + 1
        if len(bars) < min_bars:
            return 0

        df = pd.DataFrame([b.model_dump() for b in bars]).set_index("timestamp")

        # Mean reversion signal: tanh(-z_score)
        rolling_mean = df["close"].rolling(self.mean_reversion_period).mean()
        rolling_std = df["close"].rolling(self.mean_reversion_period).std()
        z_score = (df["close"] - rolling_mean) / rolling_std.replace(0, np.nan)
        mean_reversion_signal = np.tanh(-z_score)  # Negative for mean reversion

        # Momentum signal: tanh(ROC)
        momentum = df["close"].pct_change(self.momentum_period)
        momentum_signal = np.tanh(momentum)

        # Combine signals with tanh_weight
        momentum_weight = 1 - self.tanh_weight
        combined_signal = (
            self.tanh_weight * mean_reversion_signal +
            momentum_weight * momentum_signal
        )

        # Get latest signal value
        latest_signal = combined_signal.iloc[-1]

        # Apply threshold to get position: -1, 0, or 1
        if abs(latest_signal) < self.position_threshold:
            position_direction = 0
        else:
            position_direction = int(np.sign(latest_signal))

        return position_direction * self.units
```

- [ ] **Step 2: Commit the strategy implementation**

```bash
git add src/strategies/tanh_strategy.py
git commit -m "feat(tanh): Add TanhStrategy with mean reversion and momentum fusion"
```

---

## Task 2: Register Strategy in Factory

**Files:**
- Modify: `src/strategies/factory.py`

- [ ] **Step 1: Import TanhStrategy in factory.py**

Add import after line 12:

```python
from src.strategies.tanh_strategy import TanhStrategy
```

- [ ] **Step 2: Register TanhStrategy in _STRATEGY_CLASSES**

Add to the dictionary at line 23:

```python
_STRATEGY_CLASSES = {
    "SMACrossoverStrategy": SMACrossoverStrategy,
    "BollingerBandsStrategy": BollingerBandsStrategy,
    "ContrarianStrategy": ContrarianStrategy,
    "TanhStrategy": TanhStrategy,
}
```

- [ ] **Step 3: Commit factory update**

```bash
git add src/strategies/factory.py
git commit -m "chore(factory): Register TanhStrategy in strategy factory"
```

---

## Task 3: Export from Module

**Files:**
- Modify: `src/strategies/__init__.py`

- [ ] **Step 1: Add TanhStrategy to exports**

Read the current `__init__.py` and add TanhStrategy to the exports:

```python
from src.strategies.tanh_strategy import TanhStrategy
```

Also add to `__all__` list if present.

- [ ] **Step 2: Commit module export**

```bash
git add src/strategies/__init__.py
git commit -m "chore(strategies): Export TanhStrategy from module"
```

---

## Task 4: Create Default Configuration

**Files:**
- Create: `config/strategies/tanh_strategy.yaml`

- [ ] **Step 1: Create YAML configuration file**

```yaml
# Tanh Strategy Configuration
# Combines mean reversion and momentum using tanh activation

# Mean reversion lookback period (bars)
mean_reversion_period: 20

# Momentum lookback period (bars)
momentum_period: 10

# Weight for mean reversion signal (0.0 - 1.0)
# Remainder (1 - tanh_weight) goes to momentum
tanh_weight: 0.6

# Minimum signal strength to trigger position (0.0 - 1.0)
# Below threshold = neutral position (0)
position_threshold: 0.3

# Position size when signal triggers
units: 10
```

- [ ] **Step 2: Commit configuration**

```bash
git add config/strategies/tanh_strategy.yaml
git commit -m "config(tanh): Add default parameters for TanhStrategy"
```

---

## Task 5: Write Unit Tests

**Files:**
- Create: `tests/strategies/test_tanh_strategy.py`

- [ ] **Step 1: Create test file with imports and fixtures**

```python
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
```

- [ ] **Step 2: Test insufficient data returns neutral**

```python
def test_insufficient_data_returns_zero(tanh_strategy):
    """Should return 0 when not enough bars."""
    # Only 3 bars, need at least max(5, 3) + 1 = 6
    bars = create_bars([100.0, 101.0, 102.0])
    position = tanh_strategy.calculate_position(bars)
    assert position == 0
```

- [ ] **Step 3: Test strong mean reversion signal (buy)**

```python
def test_strong_mean_reversion_buy_signal(tanh_strategy):
    """
    When price drops significantly below mean, should trigger buy.
    Creates a stable price then a sharp drop.
    """
    # 10 bars: stable around 100, then sharp drop
    prices = [100.0, 100.5, 99.5, 100.0, 100.2,  # Stable
              99.8, 100.1, 99.9, 95.0, 94.0]      # Sharp drop
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    # Negative z-score -> tanh(-z_score) positive -> should buy
    assert position > 0, f"Expected buy position, got {position}"
```

- [ ] **Step 4: Test strong mean reversion signal (sell)**

```python
def test_strong_mean_reversion_sell_signal(tanh_strategy):
    """
    When price spikes significantly above mean, should trigger sell.
    """
    # 10 bars: stable around 100, then sharp spike
    prices = [100.0, 100.5, 99.5, 100.0, 100.2,
              99.8, 100.1, 99.9, 105.0, 106.0]      # Sharp spike
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    # Positive z-score -> tanh(-z_score) negative -> should sell
    assert position < 0, f"Expected sell position, got {position}"
```

- [ ] **Step 5: Test neutral when signal below threshold**

```python
def test_neutral_when_signal_below_threshold(tanh_strategy):
    """
    When combined signal is weak (below threshold), should return neutral.
    """
    # Stable prices with minimal deviation
    prices = [100.0, 100.0, 100.0, 100.0, 100.0,
              100.0, 100.0, 100.0, 100.0, 100.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    # No significant movement -> signal should be below threshold
    assert position == 0, f"Expected neutral position, got {position}"
```

- [ ] **Step 6: Test momentum signal dominance**

```python
def test_momentum_signal_buy(tanh_strategy):
    """
    With tanh_weight=0 (pure momentum), strong uptrend should trigger buy.
    """
    tanh_strategy.tanh_weight = 0.0  # Pure momentum
    tanh_strategy.position_threshold = 0.2

    # Strong uptrend
    prices = [100.0, 101.0, 102.0, 103.0, 104.0,
              105.0, 106.0, 107.0, 108.0, 109.0]
    bars = create_bars(prices)

    position = tanh_strategy.calculate_position(bars)

    assert position > 0, f"Expected momentum buy, got {position}"
```

- [ ] **Step 7: Test position scaling by units**

```python
def test_position_scaled_by_units(mock_contract):
    """
    Position should be scaled by units parameter.
    """
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

    # Same price pattern: sharp drop (mean reversion buy)
    prices = [100.0, 100.5, 99.5, 100.0, 100.2,
              99.8, 100.1, 99.9, 95.0, 94.0]
    bars = create_bars(prices)

    pos_5 = strategy_5.calculate_position(bars)
    pos_10 = strategy_10.calculate_position(bars)

    assert abs(pos_10) == 10, f"Expected position 10, got {pos_10}"
    assert abs(pos_5) == 5, f"Expected position 5, got {pos_5}"
```

- [ ] **Step 8: Run all tests**

```bash
pytest tests/strategies/test_tanh_strategy.py -v
```

Expected output:
```
tests/strategies/test_tanh_strategy.py::test_insufficient_data_returns_zero PASSED
tests/strategies/test_tanh_strategy.py::test_strong_mean_reversion_buy_signal PASSED
tests/strategies/test_tanh_strategy.py::test_strong_mean_reversion_sell_signal PASSED
tests/strategies/test_tanh_strategy.py::test_neutral_when_signal_below_threshold PASSED
tests/strategies/test_tanh_strategy.py::test_momentum_signal_buy PASSED
tests/strategies/test_tanh_strategy.py::test_position_scaled_by_units PASSED
```

- [ ] **Step 9: Commit tests**

```bash
git add tests/strategies/test_tanh_strategy.py
git commit -m "test(tanh): Add comprehensive tests for TanhStrategy"
```

---

## Task 6: Update Documentation

**Files:**
- Modify: `src/strategies/README.md`

- [ ] **Step 1: Add TanhStrategy to available strategies table**

Add to the Available Strategies table:

```markdown
| `TanhStrategy` | ML-inspired mean reversion + momentum with tanh activation |
```

- [ ] **Step 2: Add configuration example**

Add after the existing strategy examples:

```markdown
### Example: `config/strategies/tanh_strategy.yaml`

```yaml
mean_reversion_period: 20
momentum_period: 10
tanh_weight: 0.6
position_threshold: 0.3
units: 10
```
```

- [ ] **Step 3: Commit documentation update**

```bash
git add src/strategies/README.md
git commit -m "docs(strategies): Add TanhStrategy to documentation"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `src/strategies/tanh_strategy.py` exists and contains TanhStrategy class
- [ ] `TanhStrategy` is imported in `src/strategies/__init__.py`
- [ ] `TanhStrategy` is registered in `_STRATEGY_CLASSES` in `src/strategies/factory.py`
- [ ] `config/strategies/tanh_strategy.yaml` exists with sensible defaults
- [ ] All tests in `tests/strategies/test_tanh_strategy.py` pass
- [ ] Can instantiate via `StrategyFactory.create("TanhStrategy", contract, config_file)`
- [ ] Strategy outputs -1, 0, or 1 (scaled by units) as expected
- [ ] Documentation is updated

---

## Design Notes

### Why Tanh?

The hyperbolic tangent (tanh) function maps any real value to the range (-1, 1):
- Bound signals into interpretable range
- Smooth transition near zero (no hard thresholds)
- Saturates at extremes (reduces impact of outliers)

### Signal Combination

Mean reversion and momentum are often opposing forces:
- Mean reversion: "Price is too high/low, revert to mean"
- Momentum: "Price is trending, follow the trend"

The `tanh_weight` parameter allows tuning which signal dominates:
- 1.0 = pure mean reversion
- 0.5 = equal weight
- 0.0 = pure momentum

### Position Threshold

The threshold prevents whipsaw trading:
- 0.0 = always in market (no neutral state)
- 0.3 = moderate threshold (recommended)
- 0.8 = very high conviction required

### Discrete Output

Standard ML classifiers output {-1, 0, 1}:
- Unlike continuous position sizing, this matches the executor's discrete signal handling
- Simplifies backtesting and analysis
- Reduces over-trading
