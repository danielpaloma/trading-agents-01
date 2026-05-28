# Trading Agents Architecture Report

## Overview

This is a multi-agent trading system that executes a trading session against Interactive Brokers (IBKR) using ib_async. The system consists of 6 specialized agents coordinated by a main orchestrator, with each agent handling a specific aspect of the trading workflow.

## Main Components

### Entry Point
- **`src/main.py`** — Async entry point that loads configuration and starts the TradingOrchestrator

### Core Orchestrator
- **`src/agents/orchestrator.py`** — TradingOrchestrator class that:
  - Manages the full trading lifecycle (connect → trade → disconnect)
  - Coordinates all agents in sequence
  - Maintains TradingSessionState
  - Handles real-time bar callbacks from IBKR

### Agents (src/agents/)

| Agent | File | Responsibility |
|------|------|----------------|
| MarketDataAgent | `market_data_agent.py` | Loads historical bars; processes real-time bar updates |
| StrategyAgent | `strategy_agent.py` | Selects between SMA / MeanReversion using market statistics + LLM |
| AnalysisAgent | `analysis_agent.py` | Computes indicators; asks LLM for trading signal |
| RiskAgent | `risk_agent.py` | Evaluates signal; computes position size, SL, TP; checks drawdown |
| ExecutionAgent | `execution_agent.py` | Places orders (bracket or simple); manages position changes |
| MonitorAgent | `monitor_agent.py` | Checks stop conditions; builds session summary |

### Tools (src/tools/)

| Tool | File | Responsibility |
|------|------|----------------|
| IBKRClient | `ibkr_tools.py` | Connects to TWS/Gateway; creates contracts; places/cancels orders |
| Analysis Tools | `analysis_tools.py` | Computes SMA, Bollinger Bands; generates rule-based signals |
| Risk Tools | `risk_tools.py` | Computes SL/TP prices, position size, drawdown check |

### Data Models (src/models/)

| Model | File | Description |
|-------|------|-------------|
| Bar | `market_data.py` | OHLCV bar with timestamp |
| OHLCVHistory | `market_data.py` | Deque-based bar storage with max_bars, to_dataframe() |
| Signal | `signals.py` | Direction (long/short/flat), strategy name, reason |
| Direction | `signals.py` | Enum: LONG, SHORT, FLAT |
| OrderFill | `orders.py` | Execution record |
| SessionSummary | `portfolio.py` | End-of-session statistics |

### State
- **`src/state.py`** — TradingSessionState dataclass holding position, price, history, P&L, session timing

### Configuration
- **`src/config.py`** — Config loader (likely from environment/JSON)

---

## Workflow Execution (4 Stages)

The system follows a structured 4-stage execution model:

### Stage 1 — Startup
```
main.py → Orchestrator.start()
  ├─ Client.connect()
  ├─ Create contract (FOREX/STOCK/CFD)
  ├─ MarketDataAgent.load_history() → historical bars → state.history
  ├─ StrategyAgent.select_strategy() → "SMA" or "MeanReversion"
  ├─ Request real-time bars (5-sec bars, MIDPOINT)
  └─ Enter main loop
```

### Stage 2 — Monitor Loop
```
Every 1 second:
  Orchestrator → MonitorAgent.check(state)
  ├─ Check session_end time reached?
  ├─ Check max drawdown exceeded?
  ├─ Check stop-loss/take-profit triggered?
  └─ Return MonitorResult(should_stop)
  If should_stop: exit loop → _shutdown()
```

### Stage 3 — Per-Bar Tick Processing (triggered by real-time bar callback)
```
RTB callback → _on_bar()
  ├─ MarketDataAgent.on_bar_update() → state.history.append(); state.current_price
  ├─ AnalysisAgent.run(state, strategy) → Signal(direction, reason)
  ├─ RiskAgent.evaluate(state, signal) → RiskDecision(approved, qty, SL, TP)
  └─ ExecutionAgent.execute(state, decision, contract, direction)
      ├─ If approved + qty changed: place_bracket_order() or placeOrder()
      ├─ If flat signal: cancel_all_orders() + close position
      └─ Update state.current_position
```

### Stage 4 — Shutdown
```
  ├─ Cancel real-time bars
  ├─ Close any open position (flat)
  ├─ MonitorAgent.build_summary() → SessionSummary
  ├─ Print summary
  └─ Client.disconnect()
```

---

## Key Design Patterns

1. **Agent Coordination**: Orchestrator holds references to all agents and calls them sequentially per bar
2. **State-Driven**: Single TradingSessionState shared across agents
3. **LLM-Augmented**: StrategyAgent and AnalysisAgent use OpenRouter LLMs for decision-making
4. **Rule Fallback**: AnalysisAgent falls back to rule-based signals (sma_signal, mean_reversion_signal) if LLM fails
5. **Risk-Gated**: RiskAgent evaluates every signal before ExecutionAgent can trade
6. **Bracket Orders**: ExecutionAgent places parent + stop-loss + take-profit as a linked group

---

## Data Flow Summary

```
IBKR (TWS/Gateway)
        │
   IBKRClient
        │
  ┌────┴────┐
  │         │
MarketData  Execution
   │          │
   ├────► Orchestrator
   │          │
   │      StrategyAgent ──► LLM
   │          │
   │      AnalysisAgent ───► LLM
   │          │
   │      RiskAgent ──────► RiskDecision
   │          │
   │      Execution ────► Orders
   │          │
   └────► MonitorAgent ──► Stop/Continue
```

---

## Files Reference

```
src/
├── main.py                 # Entry point
├── config.py              # Configuration loader
├── state.py              # TradingSessionState
├── agents/
│   ├── orchestrator.py   # Main coordinator
│   ├── market_data_agent.py
│   ├── strategy_agent.py
│   ├── analysis_agent.py
│   ├── risk_agent.py
│   ├── execution_agent.py
│   └── monitor_agent.py
├── tools/
│   ├── ibkr_tools.py    # IBKRClient
│   ├── analysis_tools.py
│   └── risk_tools.py
└── models/
    ├── market_data.py  # Bar, OHLCVHistory
    ├── signals.py     # Signal, Direction
    ├── orders.py     # OrderFill
    └── portfolio.py # SessionSummary
```
