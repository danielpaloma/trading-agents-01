# Updated Order Execution Decision Tree

> After implementing the stateful position transition logic from `trader_ibkr.py`

**Key Changes:**
- Position-aware transitions (NEUTRAL ↔ LONG ↔ SHORT)
- Cancel existing SL/TP before position changes
- Close-to-neutral first with MarketOrder, then open with BracketOrder
- Track expected vs actual position for SL/TP hit detection

---

## Main Loop: SL/TP Hit Detection

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MAIN TRADING LOOP (every 5 seconds)                                    │
│  File: src/strategies/main.py:148+                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  REFRESH MARKET DATA                                                    │
│  • Fetch historical bars (1 day)                                        │
│  • Update state.history and state.current_price                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  COMPUTE NEW TARGET                                                     │
│  target = executor.compute_target(state)                                │
│  Example: -10 (SHORT 10 units)                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  GET CURRENT POSITION                                                   │
│  current_pos = get_current_position(client, contract)                   │
│  Example: 0 (NEUTRAL)                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ target == current_pos │       │ target != current_pos │
        │ (Position aligned)    │       │ (Position mismatch)   │
        └───────────────────────┘       └───────────────────────┘
                    │                               │
                    ▼                               ▼
        ┌───────────────────────┐       ┌───────────────────────┐
        │ SKIP TRADE            │       │ CHECK FOR SL/TP HIT   │
        │ Log: "Position        │       │                       │
        │  unchanged"           │       │ See Section 4 below   │
        └───────────────────────┘       └───────────────────────┘
                                                    │
                                                    ▼
                                        ┌───────────────────────┐
                                        │ CHECK: Is this an     │
                                        │ expected SL/TP hit?   │
                                        │                       │
                                        │ state.expected_pos    │
                                        │   != current_pos?     │
                                        └───────────────────────┘
                                                    │
                            ┌───────────────────────┴───────────────────────┐
                            │                                               │
                            ▼ YES                                           ▼ NO
                ┌───────────────────────┐                       ┌───────────────────────┐
                │ SL/TP EVENT DETECTED  │                       │ NORMAL REBALANCE      │
                │                       │                       │ (Strategy signal      │
                │ expected=-10,         │                       │  changed)             │
                │ actual=0              │                       │                       │
                └───────────────────────┘                       │ Execute:              │
                            │                                   │ execute_trade(...)    │
                            ▼                                   └───────────────────────┘
                ┌───────────────────────┐                                   │
                │ 1. Clear active       │                                   │
                │    SL/TP references   │                                   ▼
                │ 2. Close any          │                       ┌───────────────────────┐
                │    remaining position │                       │ See Section 2 below   │
                │ 3. Set expected_pos=0 │                       │ (Position Transitions)│
                │ 4. Continue/Restart   │                       └───────────────────────┘
                └───────────────────────┘
```

---

## 1. execute_trade() - Entry Point

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EXECUTE_TRADE() FUNCTION                                               │
│  File: src/strategies/main.py                                           │
│  Signature: execute_trade(client, contract, target, current_pos,        │
│                          config, state)  # NEW: state parameter         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  INPUTS                                                                 │
│  ─────────────────────────────────────────────────────────────────────  │
│  • target: Desired position (-10 = SHORT 10, +10 = LONG 10, 0 = FLAT)   │
│  • current_pos: Actual position from IBKR                               │
│  • state: TradingSessionState (tracks expected_position, active SL/TP)  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CALCULATE TRADE SIZE                                                   │
│  trades = target - current_pos                                          │
│                                                                         │
│  Examples:                                                              │
│  • target=-10, current=0  → trades=-10 (need to SELL 10)                │
│  • target=+10, current=-5 → trades=+15 (need to BUY 15)                 │
│  • target=0,  current=+5  → trades=-5  (need to SELL 5)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │ trades == 0   │               │ trades != 0   │
            │ (No change)   │               │ (Action needed│
            └───────────────┘               └───────────────┘
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │ SKIP          │               │ ROUTE TO      │
            │ return early  │               │ TRANSITION    │
            └───────────────┘               │ LOGIC         │
                                            └───────────────┘
                                                            │
                                                            ▼
                                            ┌───────────────┴───────────────┐
                                            │ GET CURRENT PRICE             │
                                            │                               │
                                            │ current_price =               │
                                            │  client.get_current_price()   │
                                            └───────────────────────────────┘
                                                            │
                                    ┌───────────────────────┴───────────────────────┐
                                    │                                               │
                                    ▼ price ≤ 0                                     ▼ price > 0
                            ┌───────────────┐                               ┌───────────────┐
                            │ STREAM ISSUE: │                               │ NORMAL FLOW:  │
                            │ No price      │                               │ Calculate     │
                            │ available     │                               │ SL/TP prices  │
                            │               │                               │               │
                            │ Possible:     │                               │ sl_price,     │
                            │ • Disconnect  │                               │ tp_price =    │
                            │ • Stale data  │                               │ calculate_    │
                            │ • API error   │                               │   sl_tp_      │
                            │               │                               │   prices()    │
                            │ ACTION:       │                               │               │
                            │ Skip trade,   │                               │               │
                            │ keep current  │                               │               │
                            │ position      │                               │               │
                            │               │                               │               │
                            │ Log: "No      │                               │               │
                            │ valid price   │                               │               │
                            │ (potential    │                               │               │
                            │ stream        │                               │               │
                            │ disconn...    │                               │               │
                            │ Skipping..."  │                               │               │
                            └───────────────┘                               └───────────────┘
                                    │                                               │
                                    ▼                                               ▼
                            ┌───────────────┐                               ┌───────────────┐
                            │ RETURN EARLY  │                               │ ROUTE BASED   │
                            │ Position      │                               │ ON TARGET     │
                            │ unchanged     │                               │ See Section 2 │
                            └───────────────┘                               └───────────────┘
```

---

## 2. Position Transition Logic

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ROUTING BY TARGET POSITION                                             │
│  Based on: target > 0, target < 0, or target == 0                       │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │                                                                  │
    ▼ target > 0                                                     ▼ target < 0
┌─────────────────────┐                                    ┌─────────────────────┐
│ GOING LONG          │                                    │ GOING SHORT         │
│ target = +10        │                                    │ target = -10        │
│ action = "BUY"      │                                    │ action = "SELL"     │
│ qty = 10            │                                    │ qty = 10            │
└─────────────────────┘                                    └─────────────────────┘
         │                                                          │
         ▼                                                          ▼
┌─────────────────────┐                                    ┌─────────────────────┐
│ CHECK current_pos   │                                    │ CHECK current_pos   │
└─────────────────────┘                                    └─────────────────────┘
         │                                                          │
    ┌────┴────┬────────────┬                               ┌────┴────┬────────────┐
    │         │            │                               │         │            │
    ▼         ▼            ▼                               ▼         ▼            ▼
┌───────┐ ┌────────┐  ┌─────────┐                      ┌───────┐ ┌─────────┐  ┌────────┐
│ == 0  │ │ < 0    │  │ > 0     │                      │ == 0  │ │ > 0     │  │ < 0    │
│NEUTRAL│ │SHORT   │  │LONG     │                      │NEUTRAL│ │LONG     │  │SHORT   │
│       │ │(flipping│  │(already │                      │       │ │(flipping│  │(already│
│       │ │ short)  │  │ long)   │                      │       │ │ long)   │  │ short)  │
└───┬───┘ └────┬───┘  └───┬─────┘                      └───┬───┘ └────┬────┘  └───┬────┘
    │          │          │                                │          │          │
    ▼          ▼          ▼                                ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                             │
│  CASE A: NEUTRAL → LONG (or SHORT)                     CASE B: OPPOSITE SIDE → FLIP        │
│  ─────────────────────────────────                     ────────────────────────────        │
│                                                                                             │
│  Direct open with bracket:                              1. CANCEL EXISTING SL/TP            │
│                                                                                             │
│  open_position_with_bracket(                            client.cancel_bracket_orders(       │
│    client, contract,                                      state.active_sl,                 │
│    action="BUY", qty=10,                                  state.active_tp)                 │
│    sl_price, tp_price,                                state.active_sl = None              │
│    state                                              state.active_tp = None              │
│  )                                                                                          │
│  └→ Stores SL/TP order refs in state                  2. CLOSE TO NEUTRAL                  │
│                                                                                             │
│                                                         close_to_neutral(                   │
│  Update:                                                client, contract,                   │
│  state.expected_position = target                       current_pos)                        │
│                                                                                             │
│  Result: Position open with SL/TP                       3. OPEN NEW POSITION               │
│  bracket attached                                       open_position_with_bracket(...)    │
│  (parent + SL child + TP child)                                                           │
│                                                                                             │
│                                                         Update:                             │
│                                                         state.expected_pos = target         │
│                                                                                             │
│                                                         Result: Position flipped,           │
│                                                         new SL/TP bracket attached          │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                                              │
                                              ▼ target == 0
                                   ┌─────────────────────┐
                                   │ GOING NEUTRAL       │
                                   │ target = 0          │
                                   │ (close position)    │
                                   └─────────────────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │ CHECK current_pos   │
                                   └─────────────────────┘
                                              │
                                    ┌─────────┴─────────┐
                                    │                   │
                                    ▼ > 0               ▼ < 0
                            ┌───────────────┐   ┌───────────────┐
                            │ From LONG     │   │ From SHORT    │
                            └───────┬───────┘   └───────┬───────┘
                                    │                   │
                                    ▼                   ▼
                            ┌───────────────────────────────────┐
                            │ CASE C: CLOSE TO NEUTRAL          │
                            │ ─────────────────────────         │
                            │                                   │
                            │ 1. CANCEL EXISTING SL/TP          │
                            │    client.cancel_bracket_orders() │
                            │    state.active_sl = None         │
                            │    state.active_tp = None         │
                            │                                   │
                            │ 2. CLOSE POSITION                 │
                            │    close_to_neutral(              │
                            │      client, contract,            │
                            │      current_pos)                 │
                            │    └→ Uses MarketOrder            │
                            │                                   │
                            │ Update:                           │
                            │ state.expected_position = 0       │
                            │                                   │
                            │ Result: Position closed,          │
                            │ no SL/TP orders active            │
                            └───────────────────────────────────┘
```

---

## 3. Helper Functions Detail

### 3.1 close_to_neutral()

```
┌─────────────────────────────────────────────────────────────────────────┐
│  close_to_neutral(client, contract, current_pos)                        │
│  ─────────────────────────────────────────────────────────────────────  │
│  PURPOSE: Close current position using MarketOrder (fast execution)     │
│                                                                         │
│  INPUT:                                                                 │
│  • current_pos: Current position (positive=long, negative=short)        │
│                                                                         │
│  LOGIC:                                                                 │
│  if current_pos == 0: return (nothing to do)                            │
│                                                                         │
│  action = "BUY"  if current_pos < 0  (closing short)                    │
│         = "SELL" if current_pos > 0  (closing long)                     │
│  qty = abs(current_pos)                                                 │
│                                                                         │
│  order = MarketOrder(action, qty)                                       │
│  client.ib.placeOrder(contract, order)                                  │
│                                                                         │
│  LOG: "Closing position: {action} {qty} to go NEUTRAL"                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 open_position_with_bracket()

```
┌─────────────────────────────────────────────────────────────────────────┐
│  open_position_with_bracket(client, contract, action, qty,              │
│                            sl_price, tp_price, state)                   │
│  ─────────────────────────────────────────────────────────────────────  │
│  PURPOSE: Open new position with SL/TP child orders                     │
│                                                                         │
│  STEPS:                                                                 │
│  1. Create BracketOrder via client:                                     │
│     trades = client.place_bracket_order_with_tracking(                  │
│                contract, action, qty, sl_price, tp_price)               │
│     └→ Returns [parent_trade, stop_trade, tp_trade]                     │
│                                                                         │
│  2. Store order references in state:                                    │
│     state.active_stop_loss = trades[1].order  (if exists)               │
│     state.active_take_profit = trades[2].order  (if exists)             │
│                                                                         │
│  3. Log opening:                                                        │
│     "Opened {action} position: {action} {qty} |                         │
│      SL: {sl_price} | TP: {tp_price}"                                   │
│                                                                         │
│  BRACKET ORDER STRUCTURE:                                               │
│  ┌───────────────┐                                                      │
│  │ Parent Order  │  MarketOrder (entry)                                  │
│  │ transmit=False│                                                      │
│  └───────┬───────┘                                                      │
│          │ parentId                                                     │
│    ┌─────┴─────┐                                                        │
│    ▼           ▼                                                        │
│ ┌───────┐  ┌───────┐                                                    │
│ │ Stop  │  │ Limit │                                                    │
│ │ Loss  │  │ (TP)  │                                                    │
│ │ STP   │  │ LMT   │                                                    │
│ │transmit│  │transmit│                                                   │
│ │=False │  │=True  │  ← Only TP transmits (submits all)                  │
│ │if TP  │  │       │                                                    │
│ └───────┘  └───────┘                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 calculate_sl_tp_prices()

```
┌─────────────────────────────────────────────────────────────────────────┐
│  calculate_sl_tp_prices(current_price, target, sl_pct, tp_pct)          │
│  ─────────────────────────────────────────────────────────────────────  │
│  RETURNS: (sl_price, tp_price) tuple                                    │
│                                                                         │
│  IF target > 0 (LONG):                                                  │
│    sl_price = round(current_price × (1 - sl_pct), 5)                    │
│    tp_price = round(current_price × (1 + tp_pct), 5)                    │
│                                                                         │
│  IF target < 0 (SHORT):                                                 │
│    sl_price = round(current_price × (1 + sl_pct), 5)                    │
│    tp_price = round(current_price × (1 - tp_pct), 5)                    │
│                                                                         │
│  Example (LONG, price=1.17, sl=0.005, tp=0.01):                         │
│    SL = 1.17 × 0.995 = 1.16415 ≈ 1.1642                                 │
│    TP = 1.17 × 1.010 = 1.18170 ≈ 1.1817                                 │
│                                                                         │
│  Example (SHORT, price=1.17, sl=0.005, tp=0.01):                        │
│    SL = 1.17 × 1.005 = 1.17585 ≈ 1.1759                                 │
│    TP = 1.17 × 0.990 = 1.15830 ≈ 1.1583                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. SL/TP Hit Detection (Main Loop)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SL/TP EVENT DETECTION                                                  │
│  ─────────────────────────────────────────────────────────────────────  │
│  TRIGGER: state.expected_position != current_pos                        │
│  (Position changed without strategy signal - likely SL/TP triggered)    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  DETECTION LOGIC                                                        │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  if state.expected_position != 0 and                                    │
│     current_pos != state.expected_position:                             │
│                                                                         │
│      # SL/TP was hit!                                                   │
│      logger.warning("SL/TP EVENT: expected %.2f, actual %.2f",          │
│                      state.expected_position, current_pos)              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  HANDLING ACTIONS                                                       │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  1. CLEAR ACTIVE ORDER REFERENCES                                       │
│     state.active_stop_loss = None                                       │
│     state.active_take_profit = None                                     │
│     (Orders were triggered by IBKR, no need to cancel)                  │
│                                                                         │
│  2. CLOSE ANY REMAINING POSITION                                        │
│     if current_pos != 0:                                                │
│         close_to_neutral(client, contract, current_pos)                 │
│                                                                         │
│  3. RESET EXPECTED POSITION                                             │
│     state.expected_position = 0                                         │
│                                                                         │
│  4. DECISION POINT                                                      │
│     ┌─────────────────────────────────────────────────────────────┐     │
│     │ Option A: Stop session                                      │     │
│     │   break loop                                                │     │
│     │   (Conservative - stop after SL/TP hit)                     │     │
│     │                                                             │     │
│     │ Option B: Continue trading                                  │     │
│     │   allow loop to continue                                    │     │
│     │   strategy will compute new target                          │     │
│     │   (Aggressive - resume with new signal)                     │     │
│     └─────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Session End Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SESSION END HANDLING                                                   │
│  File: src/strategies/main.py:199+                                      │
│  Trigger: datetime.now() >= session_end                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: CANCEL ACTIVE ORDERS                                           │
│  ─────────────────────────────────────────────────────────────────────  │
│  Cancel any pending SL/TP orders before closing position:               │
│                                                                         │
│  client.cancel_bracket_orders(                                          │
│      state.active_stop_loss,                                            │
│      state.active_take_profit                                           │
│  )                                                                      │
│  state.active_stop_loss = None                                          │
│  state.active_take_profit = None                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: CLOSE POSITION WITH MARKET ORDER                               │
│  ─────────────────────────────────────────────────────────────────────  │
│  final_pos = get_current_position(client, contract)                     │
│  close_to_neutral(client, contract, final_pos)                          │
│  └→ Uses MarketOrder for fastest execution at session end               │
│                                                                         │
│  state.expected_position = 0                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: WAIT FOR FILLS                                                 │
│  await asyncio.sleep(10)  # Allow time for order execution              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: FINAL REPORTING                                                │
│  log_final_report(position_tracker, session_start)                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Comparison: Original vs Updated

| Aspect | Original (Current) | Updated (After Plan) |
|--------|-------------------|----------------------|
| **Position Transition** | Direct order: `target - current_pos` | State-aware: Cancel → Close neutral → Open new |
| **Long from Short** | Single SELL 15 order | Cancel SL/TP, BUY 5 to close, BUY 10 to open |
| **Order Tracking** | None | Store SL/TP order references in state |
| **Order Cancellation** | N/A | Cancel existing SL/TP before position change |
| **Position Close** | Same bracket order | Dedicated MarketOrder for speed |
| **SL/TP Detection** | None | Detect `expected_pos != actual_pos` |
| **Session End** | `execute_trade(target=0)` | Cancel SL/TP, then `close_to_neutral()` |
| **Fallback (no price)** | MarketOrder without SL/TP | Same |

---

## 7. State Management Summary

```python
# TradingSessionState additions for tracking
tracking_session_state = {
    # Original fields
    "current_position": 0.0,      # Actual position from IBKR
    "current_price": 0.0,
    "history": OHLCVHistory(),
    
    # NEW: Order tracking
    "expected_position": 0.0,      # Position we think we have
    "active_stop_loss": Order,     # Reference to SL order (for cancellation)
    "active_take_profit": Order,   # Reference to TP order (for cancellation)
}

# Expected vs Actual position comparison
if state.expected_position != current_position:
    # Either:
    # - SL/TP hit (expected != 0, actual moved toward 0)
    # - Strategy signal changed (normal rebalance)
```

---

*Updated Decision Tree for: align-order-placement-logic-plan.md*  
*Reference: context/references/algo-trading-course/trader_ibkr.py*
