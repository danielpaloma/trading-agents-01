
## 10. IBKR Terminology Definitions

This section provides definitions from the Interactive Brokers glossary for key terms used in this report, ensuring consistency with IBKR's standard vocabulary.

### 10.1 Order Types

| Term | IBKR Definition |
|------|-----------------|
| **Market Order (MKT)** | A market order is the most basic and commonly used type of trade order. It instructs a broker to buy or sell a security immediately at the best available current price. Market orders are typically executed quickly during normal trading hours, making them ideal for investors who prioritize speed and certainty of execution over price precision. Unlike limit orders, market orders do not guarantee a specific execution price. |
| **Stop Order (STP)** | An instruction to submit a buy or sell market order if and when a user-specified stop trigger price is attained or penetrated. A Sell Stop order is always placed below the current market price and is typically used to limit a loss or protect a profit on a long stock position. A Buy Stop order is always placed above the current market price. |
| **Limit Order (LMT)** | An order to buy or sell an instrument at a specified price or better. A buy limit order sets the maximum price the investor is willing to pay; the order will only execute at that price or lower. A sell limit order sets the minimum price the investor is willing to accept; the order will only execute at that price or higher. |
| **Bracket Order** | An order type designed to help limit your loss and lock in a profit by "bracketing" an order with two opposite-side orders. A buy order is bracketed by a high-side sell limit order and a low-side sell stop order. A sell order is bracketed by a high-side buy stop order and a low-side buy limit order. |
| **Parent Order** | The primary order in a bracket order structure. When the parent order fills, the attached child orders (stop loss and take profit) become active. |
| **Child Order** | Secondary orders attached to a parent order. In a bracket order, these are the stop loss and take profit orders. When either child order fills, the other is automatically cancelled (OCA behavior). |

### 10.2 Instruments and Contracts

| Term | IBKR Definition |
|------|-----------------|
| **Contract for Difference (CFD)** | A derivative where the price is 'derived' from the value of a reference asset or rate. The underlying of an IBKR CFD may be an equity instrument (such as a share), an index, or the exchange rate of a currency pair. IBKR CFDs are over-the-counter (OTC) products, meaning the CFD is a contract between you and IBKR as the product issuer. |
| **Forex (FX)** | The foreign exchange market where currencies are traded. IBKR offers forex trading through various currency pairs. |
| **Contract ID (conId)** | A unique identifier assigned by IBKR to each security or contract available for trading. Used to uniquely identify instruments across all IBKR systems. |

### 10.3 Positions and Trading

| Term | IBKR Definition |
|------|-----------------|
| **Position** | The number of shares or contracts an investor holds. A long position means the investor owns the security; a short position means the investor has sold short and owes the security. |
| **Long Position** | A position where the investor has purchased a security with the expectation that the price will rise. |
| **Short Position** | A position created by selling a security that the investor does not own, with the expectation that the price will decline, allowing the investor to buy back at a lower price. |
| **Neutral/Flat** | A position where the investor holds no securities (no long or short exposure). |
| **Realized Profit and Loss (Realized PnL)** | The profit or loss that is locked in when a position is closed. This is calculated as the difference between the entry price and exit price, minus any commissions. |
| **Unrealized PnL** | The profit or loss on an open position that has not yet been closed. It fluctuates with market price changes. |

### 10.4 Risk Management

| Term | IBKR Definition |
|------|-----------------|
| **Stop Loss** | An order designed to limit loss on a position. A sell stop order is placed below the current market price to limit loss or protect profit on a long position. |
| **Take Profit / Profit Taker** | An order designed to lock in profits when a specified price level is reached. Typically implemented as a limit order on the opposite side of the entry. |
| **Trailing Stop** | A dynamic exit strategy that allows investors to set a stop-loss level that adjusts automatically with the movement of a security's price. Unlike a fixed stop-loss, a trailing stop "trails" the market price by a specific percentage or dollar amount. |

### 10.5 Data and Execution

| Term | IBKR Definition |
|------|-----------------|
| **Historical Data** | Past market data that can be requested through IBKR's API for analysis and strategy development. |
| **Real-time Data Stream** | Live market data pushed to the client as new data becomes available, used for real-time trading. |
| **Regular Trading Hours (RTH)** | The standard trading hours for an exchange, typically 9:30 AM to 4:00 PM ET for US markets. |
| **Fill / Execution** | The completion of an order when it is matched with a counterparty at a specific price. |
| **Commission Report** | A report detailing the commissions and fees charged for trades. |

---

## 11. IBKR Terminology Mapping

This section maps the terminology used in the script and diagram to the official IBKR glossary terms.

### 11.1 Script-to-Glossary Mapping

| Script Term | IBKR Glossary Term | Notes |
|------------|-------------------|-------|
| `IB()` | IB Connection | Interactive Brokers API connection object |
| `Forex('EURUSD')` | Forex | Currency pair contract for EUR/USD |
| `CFD("EUR", "USD")` | Contract for Difference (CFD) | Forex CFD providing exposure to EUR/USD |
| `reqHistoricalData()` | Historical Data | Request for historical market data |
| `whatToShow='MIDPOINT'` | Midpoint | Mid-point between bid and ask prices |
| `useRTH=True` | Regular Trading Hours (RTH) | Restrict data to regular market hours |
| `keepUpToDate=True` | Real-time Data Stream | Streaming data updates |
| `MarketOrder` | Market Order (MKT) | Order to buy/sell at current market price |
| `BracketOrder` | Bracket Order | Parent order with attached SL/TP children |
| `orderType = "MKT"` | Market Order | IBKR order type code |
| `orderType = "STP"` | Stop Order | IBKR order type code |
| `orderType = "LMT"` | Limit Order | IBKR order type code |
| `stopLossPrice` | Stop Loss | Price trigger for stop loss order |
| `takeProfitPrice` | Take Profit (Profit Taker) | Price trigger for take profit order |
| `auxPrice` | Auxiliary Price | Used for stop price (STP orders) |
| `lmtPrice` | Limit Price | Used for limit price (LMT orders) |
| `transmit` | Transmit | Order transmission flag - determines when order goes to market |
| `parentId` | Parent Order ID | Links child orders to parent |
| `ib.positions()` | Position | Current open positions |
| `conId` | Contract ID | Unique identifier for instrument |
| `ib.fills()` | Fill / Execution | Completed trade executions |
| `realizedPNL` | Realized Profit and Loss | Locked-in profit/loss from closed positions |
| `cancelOrder()` | Cancel Order | Remove pending order from market |

### 11.2 Diagram-to-Glossary Mapping

| Diagram Term | IBKR Glossary Term | Notes |
|--------------|-------------------|-------|
| Session Initialization | Session | Trading session setup and connection |
| Data Stream | Real-time Data Stream | Live market data feed |
| Bracket Order | Bracket Order | Parent with SL/TP children |
| Parent: MKT Order | Parent Order | Primary market order |
| Child1: STP Order | Stop Order | Attached stop loss |
| Child2: LMT Order | Take Profit (Profit Taker) | Attached take profit |
| LONG | Long Position | Buying expecting price rise |
| SHORT | Short Position | Selling expecting price decline |
| NEUTRAL | Neutral / Flat | No open position |
| SL/TP Event | Stop Loss / Take Profit Trigger | Exit condition reached |
| exp_pos | Expected Position | Strategy's target position |
| current_pos | Position | Actual open position |
| Closing Position | Close Position | Exiting all open contracts |
| Disconnect | Disconnect | Terminating API connection |

### 11.3 Report Term Standardization

| Original Report Term | Standardized IBKR Term |
|---------------------|----------------------|
| "Going LONG" | Entering a Long Position |
| "Going SHORT" | Entering a Short Position |
| "Going NEUTRAL" | Closing Position / Flat |
| "Bracket Order (MKT + STP + LMT)" | Bracket Order with Market Parent, Stop Loss Child, and Take Profit Child |
| "Transmit Logic" | Order Transmission |
| "State Transition" | Position Transition |
| "Log Returns" | Log Returns (financial calculation) |
| "Rolling Mean" | Moving Average |
| "Session Stop" | Session Termination |
| "Trade Fills" | Fills / Executions |

---

*Generated for FT004: Initial Decision Tree Analysis*  
*Date: 2026-05-05*
