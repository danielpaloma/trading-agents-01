# Algorithmic Trading System — Component Report (from `context/references/algo-trading-course`)

## Scope & source

This report synthesizes the **components of an algorithmic trading system** as implied by:

- `context/references/algo-trading-course/course-contents.md` (course-level topics: instruments, data, strategy research, live trading, error handling, deployment/ops)
- `context/references/algo-trading-course/SMABacktester.py` (vectorized research/backtesting + parameter optimization)
- `context/references/algo-trading-course/MeanRevBacktester.py` (vectorized mean-reversion backtesting + parameter optimization)
- `context/references/algo-trading-course/trader.py` (live-ish execution loop on IBKR with a simple signal + position targeting + reporting)
- `context/references/algo-trading-course/trader_ibkr.py` (more complete live session: streaming, bracket orders (SL/TP), session stop logic, reconnection logic)

The goal is a **system view**: what building blocks you need, what each block owns, and how data and decisions flow end-to-end.

---

## 1) Core lifecycle of an algorithmic trading system

Most systems can be decomposed into three phases that share components but have different constraints:

- **Research / discovery**: explore ideas, compute features, run backtests, tune parameters, estimate risk/costs.
- **Validation**: out-of-sample tests, forward tests / paper trading, sensitivity + robustness checks.
- **Production trading**: reliable data ingestion, real-time decisioning, order execution, risk controls, monitoring, ops.

The course artifacts show this split explicitly:

- Backtesters (`SMABacktester`, `MeanRevBacktester`) are **research**-oriented: batch data, vectorized signals, simple cost model, brute-force parameter search.
- Trader scripts (`trader.py`, `trader_ibkr.py`) are **production-ish**: streaming bars, session control, order placement, SL/TP, basic reporting, basic fault handling.

---

## 2) System components (what you need, and why)

### A. Market & instrument model

**Purpose**: represent *what* you trade, its trading hours, order types, pricing conventions, and constraints.

**Responsibilities**

- **Instrument definition**: symbol/ticker, asset class (stocks/FX/CFD), currency, contract identifiers.
- **Trading session rules**: regular trading hours (RTH), weekends/bank holidays, market open/close.
- **Order semantics**: market/limit/stop, bracket orders, take-profit/stop-loss, netting vs hedging behavior.
- **Cost model inputs**: spreads, commissions, financing, slippage assumptions.

**Course tie-in**

- `course-contents.md` covers order types (market/limit/stop), SL/TP theory & pitfalls, trading hours, costs.
- `trader.py`/`trader_ibkr.py` both model the traded instrument via IBKR contracts:
  - `Forex('EURUSD')` for data request
  - `CFD("EUR", currency="USD")` for execution (and `conId` used to match positions)

**Interfaces**

- Input to **data ingestion** (what to subscribe to).
- Input to **execution** (what contract/order is valid).

---

### B. Data ingestion (historical + streaming)

**Purpose**: obtain price/volume/market data at the right granularity for research and trading.

**Responsibilities**

- **Historical retrieval** (batch):
  - read CSVs (research) or download via broker/vendor API
  - parse timestamps, timezone handling, cleaning/alignment
- **Streaming** (production):
  - subscribe to ticks or bars
  - detect new bar events
  - handle disconnections / stale streams
- **Storage** (optional but common):
  - persist raw ticks/bars for replay and debugging
  - resample (tick → bars)

**Course tie-in**

- Research backtesters read a local CSV: `"twenty_minutes.csv"`.
- Live scripts use IBKR historical bars with `keepUpToDate=True` to receive streaming bar updates.
- `trader_ibkr.py` includes a “no streaming update in last 120s” watchdog and attempts to re-establish the stream.

**Interfaces**

- Produces normalized market data frames/streams for **feature/signal computation**.
- Feeds **monitoring** (data freshness, missing data).

---

### C. Data processing & feature engineering

**Purpose**: turn raw prices into aligned, clean series and features used by strategies.

**Responsibilities**

- **Cleaning**: remove/handle NaNs, align indices, ensure correct time order.
- **Transformations**:
  - returns: simple/log returns
  - rolling statistics: SMA, rolling mean/std
  - indicators: bands, z-scores, crossovers, etc.
- **Resampling**: choose frequency for signals (e.g., 1 minute bars).

**Course tie-in**

- `SMABacktester` builds `returns`, `SMA_S`, `SMA_L` via rolling windows.
- `MeanRevBacktester` builds Bollinger-style bands (`Lower`, `Upper`) using rolling std * `dev`.
- `trader.py` and `trader_ibkr.py` compute:
  - SMA crossover (in `trader.py`)
  - sign of rolling mean of returns (contrarian/mean-reversion style) (in `trader_ibkr.py`)

**Interfaces**

- Consumed by **signal generation**.
- Input to **risk model** (volatility estimates, etc.) if used.

---

### D. Strategy / signal generation

**Purpose**: map features → desired market exposure (position) according to a trading rule.

**Responsibilities**

- Define the **signal rule** (e.g., SMA cross, Bollinger, regression, classification).
- Define **position encoding**:
  - discrete: \( \{-1, 0, +1\} \)
  - scaled: continuous position sizing (not shown in code, but common)
- Avoid common research traps:
  - look-ahead bias (signals must use only information available at the time)
  - data-snooping / overfitting (need OOS / forward testing)

**Course tie-in**

- Backtesters define `position` series and shift by 1 bar to simulate “trade on next bar”.
- `trader.py` uses the last computed `position` and multiplies by `units` to compute a **target position**.
- Course outline explicitly includes “look-ahead bias”, “in-sample vs out-of-sample”, and “forward testing”.

**Interfaces**

- Outputs a **target exposure** to the portfolio/position manager.

---

### E. Portfolio & position management (targeting + state)

**Purpose**: translate strategy intent into *actual* positions, track what you hold, and decide what to change.

**Responsibilities**

- Maintain **state**:
  - expected position (what we intended to hold)
  - current position (what broker reports)
  - last signal time / last bar time
- Convert signal to:
  - **target position** (desired net position)
  - **trade list** (delta from current to target)
- Reconcile differences between expected and actual (fills, partial fills, SL/TP triggers).

**Course tie-in**

- `trader.py`:
  - queries `ib.positions()` filtered by `conId`
  - computes `trades = target - current_pos`
  - places market orders for the delta
- `trader_ibkr.py`:
  - tracks `exp_pos` and `current_pos`
  - detects SL/TP events by comparing expected vs current position

**Interfaces**

- Sends orders to **execution**.
- Provides state to **risk** and **monitoring**.

---

### F. Risk management (pre-trade and in-trade)

**Purpose**: prevent catastrophic loss and enforce constraints regardless of strategy signal.

**Responsibilities**

- **Exposure limits**: max position size, leverage limits, concentration limits.
- **Stop conditions**: end-of-session liquidation, max drawdown, max daily loss, kill-switch.
- **Order-level controls**: stop-loss / take-profit, trailing stops, bracket orders.
- **Data / connectivity risk**: stale data, broker disconnects, unexpected gaps.

**Course tie-in**

- `trader_ibkr.py` implements:
  - bracket order construction (market parent + attached SL/TP)
  - planned session stop (time-based)
  - SL/TP event stop (position mismatch)
  - “no connection” stop if stream cannot be re-established
- Course outline covers SL/TP theory and error handling (try/except, retries, backoff, limits).

**Interfaces**

- Sits **between strategy and execution**: risk can veto/modify orders.
- Feeds **monitoring**: risk breaches, stop events, liquidation.

---

### G. Execution (order creation, routing, and lifecycle)

**Purpose**: turn desired trades into broker orders and manage their lifecycle (submit, modify, cancel, fills).

**Responsibilities**

- Create appropriate order types:
  - market orders for immediate rebalancing
  - bracket orders for SL/TP management
- Submit via broker API and handle:
  - partial fills
  - rejects
  - order status tracking
  - cancellations
- Ensure execution happens only in valid trading hours (RTH vs extended hours).

**Course tie-in**

- `trader.py` uses `MarketOrder` and `ib.placeOrder(...)`.
- `trader_ibkr.py` implements bracket orders and also attempts to cancel SL/TP legs when flipping direction.

**Interfaces**

- Consumes **trade intents** from position management + risk.
- Outputs fills/executions to **accounting/performance** and **state reconciliation**.

---

### H. Transaction cost & slippage model (research) / cost measurement (production)

**Purpose**: include realistic costs in backtests and measure realized costs in production.

**Responsibilities**

- Backtest: approximate costs via:
  - per-trade proportional cost (`tc`)
  - spread model
  - slippage model (market impact)
- Production: attribute realized PnL and costs from broker reports.

**Course tie-in**

- Backtesters subtract `trades * tc` from strategy returns at each position change.
- Trader scripts compute realized PnL from IBKR fills/commission reports:
  - build a report from `ib.fills()` and `commissionReport.realizedPNL`
  - maintain cumulative PnL

**Interfaces**

- Research: plugs into **backtester**.
- Production: plugs into **reporting/monitoring**.

---

### I. Backtesting & evaluation engine

**Purpose**: simulate strategy performance on historical data and compute metrics for comparison and selection.

**Responsibilities**

- Run backtest with correct timing (signal → next bar return).
- Compute cumulative returns and strategy equity curve.
- Compute metrics (examples from course topics):
  - CAGR, annualized return/volatility, Sharpe-like ratios, drawdowns
  - hit rate, average trade, exposure, turnover
- Provide plotting and result inspection.

**Course tie-in**

- Backtesters compute `creturns` (buy&hold) and `cstrategy` and provide plotting.
- Course outline includes broad set of financial metrics and return/risk transformations.

**Interfaces**

- Consumes **data** + **strategy**; produces results for **optimizer** and **research workflow**.

---

### J. Parameter search / optimization

**Purpose**: systematically vary strategy parameters and pick candidates to validate further.

**Responsibilities**

- Define search space (ranges, step sizes).
- Define objective (e.g., maximize terminal value, Sharpe, minimize drawdown).
- Avoid overfitting:
  - split in-sample / out-of-sample
  - use walk-forward analysis (not implemented in code but implied by course topics)

**Course tie-in**

- Both backtesters implement brute force optimization via `scipy.optimize.brute`:
  - call `update_and_run` which sets parameters and returns negative performance for minimization.

**Interfaces**

- Uses **backtester** as a function from params → score.

---

### K. Monitoring, reporting, and observability

**Purpose**: know what the system is doing, detect issues quickly, and explain performance.

**Responsibilities**

- Live reporting:
  - positions, recent signals, fills, realized/unrealized PnL
- Health checks:
  - data freshness
  - broker connectivity
  - exception rates
- Alerts:
  - risk breaches
  - session stop events
  - missing data / stalled stream

**Course tie-in**

- `trader.py` prints both the latest signal dataframe and an aggregated fill/PnL report.
- `trader_ibkr.py` uses stop messages for planned stop vs SL/TP event vs no connection.

**Interfaces**

- Cross-cutting: attached to data ingestion, risk, and execution.

---

### L. Operations: runtime, scheduling, deployment, and safety

**Purpose**: run the system reliably day after day.

**Responsibilities**

- Environment management:
  - Python/conda environments, dependencies
- Scheduling:
  - start/stop sessions on a schedule (Windows Task Scheduler, `.bat` scripts)
- Hosting:
  - local machine vs cloud VM (AWS EC2)
- Safety defaults:
  - paper trading by default
  - explicit end_time stop condition and forced flattening

**Course tie-in**

- Course outline includes AWS EC2, batch files, Task Scheduler, and stopping sessions.
- Both trader scripts include strong warnings: “paper trading only” and “check regular trading hours”.

---

## 3) Data flow: research vs production (practical view)

### Research data flow (vectorized backtests)

1. Load historical data (CSV / vendor)
2. Compute returns/features (rolling stats)
3. Generate positions (signal)
4. Compute strategy returns using lagged positions (avoid look-ahead)
5. Apply cost model (transaction costs proportional to trades)
6. Evaluate (equity curve, metrics)
7. Optimize parameters (grid/brute)
8. Validate out-of-sample / forward test (course topic)

### Production data flow (streaming + execution)

1. Connect to broker (IBKR)
2. Subscribe to bars with `keepUpToDate=True`
3. On new bar:
   - build dataframe
   - compute features + latest position
   - compute target exposure (units * signal)
   - reconcile with current position
   - submit orders (market or bracket)
4. Continuously:
   - report fills and PnL
   - enforce stop conditions (time, SL/TP event, connection loss)
5. Stop session:
   - flatten to neutral
   - cancel streams
   - final reporting and disconnect

---

## 4) Key “gotchas” highlighted by these artifacts

### Look-ahead bias is subtle

The backtesters explicitly shift position by one bar before multiplying by returns (`position.shift(1) * returns`). This is a baseline requirement for realistic timing.

### The broker is the source of truth (reconciliation matters)

`trader.py` and `trader_ibkr.py` query positions from IBKR and compute deltas to a target. This is the simplest reconciliation model. In real systems you also track:

- pending orders
- partial fills
- average fill prices
- idempotency (avoid double-submits on reconnect)

### Connectivity and data staleness are first-class risks

`trader_ibkr.py` implements a “no updates in 120 seconds” detector and attempts a re-subscribe; if it fails, it flattens and stops.

### Risk controls are part of execution, not “after the fact”

Bracket orders (SL/TP) are an execution construct. They must be correct, and “pitfalls” are common (wrong prices, wrong direction, transmit flags, parent/child ids).

---

## 5) Minimal reference architecture (component diagram in words)

If you were to implement this as a maintainable system (beyond scripts), the components typically become:

- **MarketDataService**
  - historical loader + streaming subscriber + reconnection
- **FeatureEngine**
  - transforms raw bars into features (returns, SMAs, bands, etc.)
- **Strategy**
  - produces target exposure given latest features/state
- **RiskManager**
  - validates/modifies target exposure and orders; owns stops/limits
- **Portfolio/PositionManager**
  - reconciles current holdings, computes order deltas, tracks expected position
- **ExecutionBrokerAdapter (IBKR/OANDA/FXCM)**
  - order placement, order status, fills, account/positions
- **Recorder/Store**
  - persist bars, signals, orders, fills for audit/replay
- **Reporter/Monitor**
  - PnL, health checks, alerts
- **Scheduler/Runner**
  - start/stop sessions; handles graceful shutdown and kill-switch

This decomposition matches the course progression: start with data + basic strategy + vectorized backtest, then move to a trader script with streaming + execution, then add robustness (errors, retries, SL/TP, session management, deployment).

---

## 6) What’s “still missing” (common next components)

The course outline itself hints at “what is still missing” after a basic trader script. Typical additions are:

- **Persistent storage** for ticks/bars/signals/fills (instead of printing only)
- **Proper logging** (structured logs, rotation, severity levels)
- **Configuration management** (symbols, sizing, times, credentials)
- **Secrets management** (API keys, tokens)
- **Testing harness**:
  - deterministic backtests
  - simulated broker / paper mode with replay
- **Robust evaluation**:
  - walk-forward testing
  - regime analysis
  - stress tests (gaps, latency, slippage)
- **Risk analytics** beyond SL/TP:
  - drawdown limits
  - volatility targeting
  - max turnover / max trades per hour
