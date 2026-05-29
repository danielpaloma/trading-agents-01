# Order Execution Decision Tree

This diagram illustrates the order execution flow during a trading session, mapping decisions, branches, and outcomes from the trading logic in `src/strategies/main.py`.

## Session Lifecycle Flow

```mermaid
flowchart TB
    subgraph Initialization["1. SESSION INITIALIZATION"]
        direction TB
        A[Start run_session] --> B[Load Config]
        B --> C[Connect to IBKR]
        C --> D[Create Contract]
        D --> E[Create Strategy]
        E --> F[Fetch Historical Bars
        2 days initially]
        F --> G[Initialize PositionTracker
        FIFO fill tracking]
    end

    subgraph PreSession["2. PRE-SESSION SETUP"]
        direction TB
        H[Set Session Start Time] --> I[Calculate Session End
        start + duration_hours]
        I --> J[Get Initial Position
        from IBKR]
        J --> K[Compute Initial Target
        via StrategyExecutor]
        K --> L{Position Check}
        L -->|target != current| M[Execute Initial Trade
        bracket or market order]
        L -->|target == current| N[No Trade Needed]
    end

    subgraph MainLoop["3. MAIN TRADING LOOP"]
        direction TB
        O[Loop Every 5 Seconds] --> P{End Time Reached?}
        P -->|Yes| Q[Exit Loop]
        P -->|No| R[Fetch Latest Bars
        1 day duration]
        R --> S[Update TradingState]
        S --> T[Compute New Target
        via Strategy.calculate_position]
        T --> U{Target Changed?}
        U -->|Yes| V[Execute Trade]
        U -->|No| W[Skip Execution]
        V --> X[Check for New Fills]
        W --> X
        X --> Y{New Fills?}
        Y -->|Yes| Z[Log Trade Confirmed
        Update PnL via FIFO]
        Y -->|No| O
        Z --> O
    end

    subgraph Termination["4. SESSION TERMINATION"]
        direction TB
        AA[Close All Positions] --> BB[Sell to Zero]
        BB --> CC[Wait 10 Seconds
        for final fills]
        CC --> DD[Process Remaining Fills]
        DD --> EE[Log Final Report]
        EE --> FF[Log Net PnL]
        FF --> GG[Disconnect IBKR]
        GG --> HH[End Session]
    end

    Initialization --> PreSession
    PreSession --> MainLoop
    MainLoop --> Termination

    style Initialization fill:#e1f5fe
    style MainLoop fill:#fff3e0
    style Termination fill:#ffebee
```

## Detailed Order Execution Branch

```mermaid
flowchart TB
    subgraph ExecuteTrade["EXECUTE_TRADE Function"]
        direction TB
        A1["Input: target_pos, current_pos"] --> B1["Calculate trades = target minus current"]
        B1 --> C1{"trades equals_0?"}
        C1 -->|Yes| D1["Log: No Trade Needed"]
        C1 -->|No| E1["Set Action: BUY if trades greater than 0 else SELL"]
        E1 --> F1["Set Quantity: absolute value of trades"]
        F1 --> G1["Get Current Price"]
        G1 --> H1{"Price less than or equal to 0?"}
        H1 -->|Yes| I1["Place Simple Market Order"]
        H1 -->|No| J1["Calculate SL and TP based on price plus config pct"]
        J1 --> K1["Place Bracket Order with entry SL TP"]
    end

    subgraph FillTracking["POSITION TRACKER - FIFO PnL"]
        direction TB
        L1["New Fill Received"] --> M1["Add to fills list"]
        M1 --> N1["Update PnL via _update_pnl"]
        N1 --> O1{"Match with opposite side?"}
        O1 -->|Yes| P1["Calculate Matched Qty"]
        P1 --> Q1["Compute Trade PnL: SELL minus BUY for matched qty"]
        Q1 --> R1["Add to realized_pnl"]
        O1 -->|No| S1["Skip PnL Calculation"]
        R1 --> T1["Add Commission"]
        S1 --> T1
    end

    subgraph TradeLogging["TRADE CONFIRMATION LOGGING"]
        direction TB
        U1["Check fill count change"] --> V1{"new_count greater than last_count?"}
        V1 -->|Yes| W1["Process New Fills Only"]
        W1 --> X1["Log: TRADE CONFIRMED"]
        V1 -->|No| Z1["No Logging"]
    end

    ExecuteTrade --> FillTracking
    FillTracking --> TradeLogging

    style ExecuteTrade fill:#e8f5e9
    style FillTracking fill:#f3e5f5
```

## Strategy Signal Generation (TanhStrategy Example)

```mermaid
flowchart TB
    subgraph SignalGen["STRATEGY SIGNAL CALCULATION"]
        direction TB
        A2["Input: bars list"] --> B2{"Enough bars?"}
        B2 -->|No| C2["Return Position 0"]
        B2 -->|Yes| D2["Calculate Rolling Mean"]
        D2 --> E2["Calculate Rolling StdDev"]
        E2 --> F2["Calculate Z-Score"]
        F2 --> G2["Mean Reversion Signal: tanh of minus z_score"]
        G2 --> H2["Momentum Signal: tanh of pct_change"]
        H2 --> I2["Weighted Combination"]
        I2 --> J2{"absolute value of signal greater than or equal to threshold?"}
        J2 -->|Yes| K2["Return pos_direction times units"]
        J2 -->|No| L2["Return 0 neutral position"]
    end

    style SignalGen fill:#fffde7
```

## Key Decision Points Summary

| Decision Point | Location | Condition | True Action | False Action |
|----------------|----------|-----------|-------------|--------------|
| Initial Trade | Pre-session | `target != current_pos` | Execute bracket/market order | No trade needed |
| Loop Continuation | Main loop | `datetime >= session_end` | Exit to termination | Continue trading |
| Target Changed | Main loop | `target != current_pos` | Execute trade | Skip execution |
| New Fills | Main loop | `new_fill_count > last_fill_count` | Log confirmation, update PnL | No logging |
| Price Valid | execute_trade | `current_price <= 0` | Simple market order | Bracket order with SL/TP |
| Close Position | Termination | Always | Execute sell to zero | - |

## Trade Execution Outcomes

### Order Types Used
1. **Bracket Order** (when price > 0): Entry + Stop Loss + Take Profit
2. **Market Order** (when price <= 0 or position close): Immediate execution

### Position Values
- `-10`: Short position (sell)
- `0`: Neutral/flat
- `+10`: Long position (buy)

### PnL Calculation Method
- **FIFO matching**: New fills matched against opposite-side fills in order received
- **Realized PnL**: Calculated only on closed positions (matched quantities)
- **Commission**: Tracked separately per fill
- **Net PnL**: Realized PnL - Total Commissions
