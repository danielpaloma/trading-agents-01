# Align Order Placement Logic with trader_ibkr.py

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the stateful order management, SL/TP tracking, and position transition logic from `trader_ibkr.py` into `src/strategies/main.py` and `src/tools/ibkr_tools.py`.

**Architecture:** Add stateful position tracking with explicit SL/TP order references. When changing positions, cancel existing child orders first, close to neutral with MarketOrder, then open new position with BracketOrder. Handle SL/TP hit detection in the main loop.

**Tech Stack:** Python 3.12+, ib_async, dataclasses for state

---

## File Structure

| File | Responsibility |
|------|----------------|
| `src/strategies/main.py` | Main trading loop, position state management, SL/TP event detection |
| `src/tools/ibkr_tools.py` | Order placement functions, SL/TP order tracking, cancellation |
| `src/state.py` | Extended TradingSessionState with active order tracking |

---

## Task 1: Extend State to Track Active Orders

**Files:**
- Modify: `src/state.py`

Add tracking for active SL/TP orders so they can be cancelled later.

- [ ] **Step 1: Add Order import and active_orders field**

```python
# src/state.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from src.models.market_data import OHLCVHistory
from src.models.signals import Signal
from src.models.orders import OrderFill

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

    # NEW: Track active SL/TP orders for cancellation
    active_stop_loss: Any | None = None  # ib_async Order object
    active_take_profit: Any | None = None  # ib_async Order object
    expected_position: float = 0.0  # Track expected vs actual position
```

- [ ] **Step 2: Commit**

```bash
git add src/state.py
git commit -m "feat(state): add active SL/TP order tracking and expected position"
```

---

## Task 2: Add Order Cancellation to IBKRClient

**Files:**
- Modify: `src/tools/ibkr_tools.py`

Add method to cancel existing orders.

- [ ] **Step 1: Add cancel_order and cancel_bracket_orders methods**

```python
# src/tools/ibkr_tools.py - Add after line 101

def cancel_order(self, order) -> bool:
    """Cancel a single order if it exists."""
    if order is None:
        return False
    try:
        self.ib.cancelOrder(order)
        return True
    except Exception:
        return False

def cancel_bracket_orders(self, stop_loss_order, take_profit_order) -> tuple[bool, bool]:
    """Cancel SL/TP orders, return (sl_cancelled, tp_cancelled)."""
    sl_cancelled = self.cancel_order(stop_loss_order)
    tp_cancelled = self.cancel_order(take_profit_order)
    return sl_cancelled, tp_cancelled
```

- [ ] **Step 2: Commit**

```bash
git add src/tools/ibkr_tools.py
git commit -m "feat(ibkr): add order cancellation methods for SL/TP management"
```

---

## Task 3: Refactor execute_trade with Stateful Transitions

**Files:**
- Modify: `src/strategies/main.py`
- Test: Verify changes compile

Replace the simple `execute_trade` function with state-aware logic matching `trader_ibkr.py`.

- [ ] **Step 1: Add helper function to close to neutral**

Add before `execute_trade` (around line 48):

```python
def close_to_neutral(client: IBKRClient, contract, current_pos: float) -> None:
    """Close current position using MarketOrder."""
    if current_pos == 0:
        return

    action = "BUY" if current_pos < 0 else "SELL"  # Opposite to close
    qty = abs(current_pos)

    order = MarketOrder(action, qty)
    client.ib.placeOrder(contract, order)
    logger.info("Closing position: %s %.2f to go NEUTRAL", action, qty)
```

- [ ] **Step 2: Add helper function to open new position with bracket**

```python
def open_position_with_bracket(
    client: IBKRClient,
    contract,
    action: str,
    qty: float,
    sl_price: float | None,
    tp_price: float | None,
    state: TradingSessionState
) -> None:
    """Open new position with SL/TP bracket order."""

    # Use place_bracket_order which handles Order object creation
    trades = client.place_bracket_order_with_tracking(
        contract, action, qty, sl_price, tp_price
    )

    # Store references to SL/TP orders for later cancellation
    # trades[0] = parent, trades[1] = stop (if exists), trades[2] = limit (if exists)
    if len(trades) > 1 and trades[1]:
        state.active_stop_loss = trades[1].order
    if len(trades) > 2 and trades[2]:
        state.active_take_profit = trades[2].order

    logger.info(
        "Opened %s position: %s %.2f | SL: %s | TP: %s",
        action, action, qty,
        f"{sl_price:.5f}" if sl_price else "None",
        f"{tp_price:.5f}" if tp_price else "None"
    )
```

- [ ] **Step 3: Replace execute_trade with stateful version**

Replace the entire `execute_trade` function (lines 49-80) with:

```python
def calculate_sl_tp_prices(
    current_price: float,
    target: float,
    stop_loss_pct: float,
    take_profit_pct: float
) -> tuple[float | None, float | None]:
    """Calculate SL and TP prices based on target direction."""
    sl_price = None
    tp_price = None

    if stop_loss_pct and target != 0:
        if target > 0:  # LONG
            sl_price = round(current_price * (1 - stop_loss_pct), 5)
        else:  # SHORT
            sl_price = round(current_price * (1 + stop_loss_pct), 5)

    if take_profit_pct and target != 0:
        if target > 0:  # LONG
            tp_price = round(current_price * (1 + take_profit_pct), 5)
        else:  # SHORT
            tp_price = round(current_price * (1 - take_profit_pct), 5)

    return sl_price, tp_price


def execute_trade(
    client: IBKRClient,
    contract,
    target: float,
    current_pos: float,
    config,
    state: TradingSessionState
) -> None:
    """
    Execute trade with stateful position transitions.

    Logic flow (matching trader_ibkr.py):
    1. Calculate trades needed: target - current_pos
    2. If target == 0: close position (go neutral)
    3. If target > 0 (going LONG):
       - If from SHORT: cancel SL/TP, close position, then open LONG
       - If from NEUTRAL: open LONG with bracket
    4. If target < 0 (going SHORT):
       - If from LONG: cancel SL/TP, close position, then open SHORT
       - If from NEUTRAL: open SHORT with bracket
    """
    trades = target - current_pos

    if trades == 0:
        logger.info("No trade needed - position aligned with target")
        return

    # Get current price for SL/TP calculation
    current_price = client.get_current_price(contract)
    if current_price <= 0:
        logger.warning(
            "No valid price available (potential stream disconnection). "
            "Skipping trade, maintaining current position %.2f",
            current_pos
        )
        # Do NOT trade without price visibility - keep current position
        return

    # Calculate SL/TP prices
    sl_price, tp_price = calculate_sl_tp_prices(
        current_price, target,
        config.risk.stop_loss_pct,
        config.risk.take_profit_pct
    )

    # STATEFUL POSITION TRANSITIONS (from trader_ibkr.py logic)
    if target > 0:  # GOING LONG
        action = "BUY"
        qty = target

        if current_pos == 0:  # From NEUTRAL
            open_position_with_bracket(
                client, contract, action, qty, sl_price, tp_price, state
            )

        elif current_pos < 0:  # From SHORT: close first, then open
            # Cancel existing SL/TP
            client.cancel_bracket_orders(
                state.active_stop_loss, state.active_take_profit
            )
            state.active_stop_loss = None
            state.active_take_profit = None

            # Close to neutral
            close_to_neutral(client, contract, current_pos)

            # Open new position
            open_position_with_bracket(
                client, contract, action, qty, sl_price, tp_price, state
            )

    elif target < 0:  # GOING SHORT
        action = "SELL"
        qty = abs(target)

        if current_pos == 0:  # From NEUTRAL
            open_position_with_bracket(
                client, contract, action, qty, sl_price, tp_price, state
            )

        elif current_pos > 0:  # From LONG: close first, then open
            # Cancel existing SL/TP
            client.cancel_bracket_orders(
                state.active_stop_loss, state.active_take_profit
            )
            state.active_stop_loss = None
            state.active_take_profit = None

            # Close to neutral
            close_to_neutral(client, contract, current_pos)

            # Open new position
            open_position_with_bracket(
                client, contract, action, qty, sl_price, tp_price, state
            )

    else:  # target == 0, GOING NEUTRAL
        if current_pos < 0:  # From SHORT
            client.cancel_bracket_orders(
                state.active_stop_loss, state.active_take_profit
            )
            state.active_stop_loss = None
            state.active_take_profit = None
            close_to_neutral(client, contract, current_pos)

        elif current_pos > 0:  # From LONG
            client.cancel_bracket_orders(
                state.active_stop_loss, state.active_take_profit
            )
            state.active_stop_loss = None
            state.active_take_profit = None
            close_to_neutral(client, contract, current_pos)

    # Update expected position after successful order placement
    state.expected_position = target
```

- [ ] **Step 4: Update ibkr_tools.py with new bracket method**

Modify `src/tools/ibkr_tools.py` to return the Trade objects for tracking:

```python
# Replace place_bracket_order with place_bracket_order_with_tracking

def place_bracket_order_with_tracking(
    self,
    contract,
    action: str,
    quantity: float,
    stop_loss: float | None,
    take_profit: float | None,
) -> list:
    """
    Place bracket order and return Trade objects for tracking.
    Returns list: [parent_trade, stop_trade|None, tp_trade|None]
    """
    parent = MarketOrder(action, quantity)
    parent.transmit = False

    trades = []
    parent_trade = self.ib.placeOrder(contract, parent)
    trades.append(parent_trade)

    # Stop Loss child order
    if stop_loss:
        sl_action = "SELL" if action == "BUY" else "BUY"
        stop = StopOrder(sl_action, quantity, stop_loss)
        stop.parentId = parent.orderId
        stop.transmit = False if take_profit else True
        stop_trade = self.ib.placeOrder(contract, stop)
        trades.append(stop_trade)
    else:
        trades.append(None)

    # Take Profit child order
    if take_profit:
        tp_action = "SELL" if action == "BUY" else "BUY"
        tp = LimitOrder(tp_action, quantity, take_profit)
        tp.parentId = parent.orderId
        tp.transmit = True
        tp_trade = self.ib.placeOrder(contract, tp)
        trades.append(tp_trade)
    else:
        trades.append(None)

    return trades
```

- [ ] **Step 5: Update main.py imports**

Add import at the top of main.py:
```python
from ib_async import MarketOrder, StopOrder, LimitOrder  # Add StopOrder, LimitOrder
```

- [ ] **Step 6: Update main.py calls to execute_trade**

Find all calls to `execute_trade` and add `state` parameter:

Line 145: `execute_trade(client, contract, target, current_pos, config, state)`
Line 178: `execute_trade(client, contract, target, current_pos, config, state)`
Line 201: `execute_trade(client, contract, 0, get_current_position(client, contract), config, state)`

- [ ] **Step 7: Verify code compiles**

Run: `python -m py_compile src/strategies/main.py src/tools/ibkr_tools.py src/state.py`
Expected: No output (success)

- [ ] **Step 8: Commit**

```bash
git add src/strategies/main.py src/tools/ibkr_tools.py src/state.py
git commit -m "feat(execution): add stateful position transitions with SL/TP tracking"
```

---

## Task 4: Add SL/TP Hit Detection to Main Loop

**Files:**
- Modify: `src/strategies/main.py`

Detect when stop-loss or take-profit orders have been triggered (position changes unexpectedly).

- [ ] **Step 1: Add SL/TP event detection in trading loop**

Find the trading loop (around line 148) and add detection after position update:

```python
# Main trading loop - around line 173-180

# Check for SL/TP event (position changed unexpectedly)
if state.expected_position != 0 and current_pos != state.expected_position:
    logger.warning(
        "SL/TP EVENT DETECTED: expected %.2f, actual %.2f",
        state.expected_position, current_pos
    )

    # Clear active orders since they triggered
    state.active_stop_loss = None
    state.active_take_profit = None

    # Close any remaining position
    if current_pos != 0:
        logger.info("Closing remaining position after SL/TP")
        close_to_neutral(client, contract, current_pos)
        state.expected_position = 0
    else:
        state.expected_position = 0

    # Optional: could break here for session stop, or continue
    # For now, continue trading loop (strategy will compute new target)
```

- [ ] **Step 2: Update initial expected_position**

After the initial target calculation (around line 139), set:

```python
# Initial target position
target = executor.compute_target(state)
logger.info("Initial target position: %d units", target)
state.expected_position = target  # NEW: track expected position
```

- [ ] **Step 3: Commit**

```bash
git add src/strategies/main.py
git commit -m "feat(loop): add SL/TP hit detection and handling"
```

---

## Task 5: Update Order of Operations in Session End

**Files:**
- Modify: `src/strategies/main.py`

Ensure proper cleanup at session end matching trader_ibkr.py pattern.

- [ ] **Step 1: Update session end handling**

Find session end section (around line 199) and update:

```python
# Stop trading session
logger.info("Closing all positions...")

# Cancel any active SL/TP first
client.cancel_bracket_orders(
    state.active_stop_loss, state.active_take_profit
)
state.active_stop_loss = None
state.active_take_profit = None

# Close position with MarketOrder for faster execution
final_pos = get_current_position(client, contract)
close_to_neutral(client, contract, final_pos)

state.expected_position = 0
```

- [ ] **Step 2: Commit**

```bash
git add src/strategies/main.py
git commit -m "fix(session-end): cancel SL/TP before closing, use market order for exit"
```

---

## Task 6: Test and Verify

**Files:**
- All modified files

- [ ] **Step 1: Run type checking**

Run: `python -m py_compile src/strategies/main.py src/tools/ibkr_tools.py src/state.py`
Expected: No errors

- [ ] **Step 2: Run linting if available**

Run: `ruff check src/strategies/main.py src/tools/ibkr_tools.py src/state.py` (if ruff installed)
Expected: No critical errors

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat(execution): align order logic with trader_ibkr.py stateful approach

- Add active SL/TP order tracking in state
- Implement stateful position transitions (NEUTRAL->LONG/SHORT)
- Cancel existing orders before position changes to avoid conflicts
- Close positions with MarketOrder, open with BracketOrder
- Add SL/TP hit detection in main loop
- Proper session end cleanup"
```

---

## Summary of Key Behavior Changes

| Aspect | Current (main.py) | New (aligned with trader_ibkr.py) |
|--------|-------------------|-----------------------------------|
| **Position Transition** | Direct market order | Cancel SL/TP → Close neutral → Open new |
| **SL/TP Tracking** | None | Stored in state for cancellation |
| **Close Position** | Same as open (bracket) | Dedicated MarketOrder for speed |
| **SL/TP Detection** | None | Detect unexpected position changes |
| **Session End** | Execute trade to 0 | Cancel SL/TP, then MarketOrder close |

---

## Migration Notes

- The `execute_trade` function signature changed - now requires `state` parameter
- `place_bracket_order` renamed to `place_bracket_order_with_tracking` and returns Trade objects
- New `close_to_neutral` function for position closing
- New `calculate_sl_tp_prices` function for price calculation

*Plan created: 2026-05-04*
*Reference: context/references/algo-trading-course/trader_ibkr.py*
