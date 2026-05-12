# Trading Decision Tree Report: FT004

## Script Overview
**File:** `trader_ibkr.py`  
**Strategy:** Mean Reversion on EUR/USD  
**Instrument:** CFD (Contract for Difference) on EUR/USD  
**Timeframe:** 1-minute bars  

---

## 1. Session Initialization

### 1.1 Global Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| `freq` | "1 min" | Bar frequency for data stream |
| `window` | 1 | Rolling window for mean calculation |
| `units` | 10 | Position size multiplier |
| `end_time` | UTC_NOW + 5.5 min | Session auto-termination time |
| `sl_perc` | 0.1 (10%) | Stop Loss percentage from entry |
| `tp_perc` | 0.1 (10%) | Take Profit percentage from entry |
| `contract` | Forex('EURUSD') | Underlying for data |
| `cfd` | CFD("EUR", "USD") | Tradable instrument |

### 1.2 State Variables
| Variable | Initial | Purpose |
|----------|---------|---------|
| `exp_pos` | 0 | Expected/target position |
| `current_pos` | 0 | Actual current position |
| `last_update` | NOW | Last bar update timestamp |
| `session_start` | NOW | Session start for reporting |

---

## 2. Trading Strategy Logic

### 2.1 Signal Generation
```python
df["returns"] = np.log(df["close"] / df["close"].shift())  # Log returns
df["position"] = -np.sign(df.returns.rolling(window).mean())  # Mean reversion signal
target = df["position"][-1] * units  # Final target position
```

### 2.2 Decision Logic
| Condition | Signal | Action |
|-----------|--------|--------|
| Rolling mean returns > 0 | position = -1 | SELL (expect reversion down) |
| Rolling mean returns < 0 | position = +1 | BUY (expect reversion up) |
| Rolling mean returns = 0 | position = 0 | NO TRADE |

**Logic:** Mean reversion - if recent returns are positive (upward momentum), the strategy goes SHORT expecting a pullback. If recent returns are negative, goes LONG expecting a bounce.

---

## 3. Risk Management (SL/TP Calculation)

### 3.1 Stop Loss Rules
```
IF Target > 0 (LONG):     SL_Price = Current_Price * (1 - 0.10)
IF Target < 0 (SHORT):    SL_Price = Current_Price * (1 + 0.10)
IF Target = 0 (NEUTRAL):  SL_Price = None
```

### 3.2 Take Profit Rules
```
IF Target > 0 (LONG):     TP_Price = Current_Price * (1 + 0.10)
IF Target < 0 (SHORT):    TP_Price = Current_Price * (1 - 0.10)
IF Target = 0 (NEUTRAL):  TP_Price = None
```

### 3.3 Example Calculation
| Current Price | Target | SL_Price | TP_Price |
|---------------|--------|----------|----------|
| 1.0850 | LONG (+10) | 0.9765 | 1.1935 |
| 1.0850 | SHORT (-10) | 1.1935 | 0.9765 |

---

## 4. Trade Execution Logic

### 4.1 State Transition Matrix

| From \ To | LONG (+) | SHORT (-) | NEUTRAL (0) |
|-----------|----------|-----------|-------------|
| **NEUTRAL** | BUY Bracket Order | SELL Bracket Order | No action |
| **LONG (+)** | No action | Cancel SL/TP → SELL Close → SELL Bracket | Cancel SL/TP → SELL Close |
| **SHORT (-)** | Cancel SL/TP → BUY Close → BUY Bracket | No action | Cancel SL/TP → BUY Close |

### 4.2 Execution Flow

#### A. Going LONG from Neutral
1. Create Bracket Order (MKT + STP + LMT)
2. Submit all 3 orders linked
3. Parent (BUY MKT) fills immediately
4. Children (SELL STP/LMT) wait for SL/TP trigger

#### B. Going SHORT from Neutral
1. Create Bracket Order (MKT + STP + LMT)
2. Submit all 3 orders linked
3. Parent (SELL MKT) fills immediately
4. Children (BUY STP/LMT) wait for SL/TP trigger

#### C. Going LONG from SHORT (Flip)
1. Cancel existing SL/TP orders from short position
2. Submit Market BUY order to close short (qty = abs(current_pos))
3. Submit new Bracket Order for long position

#### D. Going SHORT from LONG (Flip)
1. Cancel existing SL/TP orders from long position
2. Submit Market SELL order to close long (qty = current_pos)
3. Submit new Bracket Order for short position

#### E. Going NEUTRAL from LONG
1. Cancel existing SL/TP orders
2. Submit Market SELL order (qty = current_pos)

#### F. Going NEUTRAL from SHORT
1. Cancel existing SL/TP orders
2. Submit Market BUY order (qty = abs(current_pos))

---

## 5. Bracket Order Structure

### 5.1 OCA (One-Cancels-All) Behavior
The bracket order consists of 3 linked orders:

```
Parent Order (MKT)
    ├── Child 1: Stop Loss (STP)
    └── Child 2: Take Profit (LMT)
```

When parent fills, both children become active. When either child fills, the other is automatically cancelled.

### 5.2 Order Parameters

| Order | Type | Action | Price | Transmit |
|-------|------|--------|-------|----------|
| Parent | MKT | BUY/SELL | Market | False* |
| SL Child | STP | Opposite | sl_price | False* |
| TP Child | LMT | Opposite | tp_price | True |

*Transmit is True if no SL/TP attached

### 5.3 Transmit Logic
- If no SL/TP: Parent transmits immediately
- If SL only: Parent transmits false, SL transmits true
- If TP only: Parent transmits false, TP transmits true
- If both SL & TP: Parent false, SL false, TP true (cascade trigger)

---

## 6. Session Stop Conditions

### 6.1 Stop Condition 1: Time Limit
**Trigger:** `datetime.now(UTC) >= end_time` (5.5 minutes after start)

**Actions:**
1. Execute trade with target = 0 (go neutral)
2. Cancel historical data stream
3. Wait 10 seconds for fills
4. Generate final trade report
5. Disconnect from IBKR
6. Print "Session Stopped (planned)"

### 6.2 Stop Condition 2: SL/TP Event
**Trigger:** `exp_pos != current_pos` (expected position differs from actual)

**Actions:**
1. Wait 5 seconds for position update
2. Verify position change persisted
3. Execute trade with target = 0 (close position)
4. Cancel historical data stream
5. Wait 10 seconds for fills
6. Generate final report
7. Disconnect
8. Print "Session Stopped (SL/TP Event)"

### 6.3 Stop Condition 3: Connection Loss
**Trigger:** No bar update received in > 120 seconds

**Actions:**
1. Cancel current data stream
2. Try to reinitialize stream
3. **If successful:** Resume normal operation
4. **If failed:**
   - Wait 5 seconds
   - Try to close any open positions
   - Wait 10 seconds
   - Generate final report (if possible)
   - Disconnect
   - Print "Session Stopped - No Connection"

---

## 7. Reporting

### 7.1 Real-time Display
- Clears console each update
- Displays current DataFrame (OHLC + position)
- Displays trade fills and PnL during session

### 7.2 Final Report Fields
| Field | Description |
|-------|-------------|
| time | Execution timestamp |
| side | BUY or SELL |
| shares | Quantity filled |
| avgPrice | Average fill price |
| realizedPNL | P&L realized on this trade |
| cumPNL | Cumulative P&L for session |

### 7.3 Report Aggregation
- Groups by time and side
- Sums shares and realized PnL
- Averages prices
- Calculates cumulative PnL

---

## 8. Key Decision Points Summary

| Decision Point | File:Line | Logic |
|----------------|-----------|-------|
| New bar? | trader_ibkr.py:59 | `bars[-1].date > last_bar` |
| Position signal | trader_ibkr.py:69 | `-np.sign(df.returns.rolling(window).mean())` |
| SL/TP calculation | trader_ibkr.py:94-108 | Direction-based percentage offset |
| Trade direction | trader_ibkr.py:111-131 | Target vs current position comparison |
| Session stop | trader_ibkr.py:228-279 | Time, SL/TP, or connection check |

---

## 9. Risk Considerations

### 9.1 Hardcoded Values
- 10% SL/TP is very aggressive for forex (typical is 0.1-1%)
- 5.5 minute session is very short for meaningful testing
- 1-unit window provides no smoothing (immediate reaction)

### 9.2 Edge Cases Handled
- Connection drops (120-second timeout)
- Position flips (cancel before entering new)
- Partial fills (monitors actual vs expected position)
- Stream interruptions (attempts reconnection)

### 9.3 Potential Issues
- No position validation before executing (assumes broker state)
- Try/except blocks swallow errors silently
- SL/TP cancellation exceptions ignored
- No maximum loss limit per session

---

---
