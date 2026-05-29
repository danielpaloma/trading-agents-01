# IB Exchange Codes Reference

This document lists the common exchange codes used in Interactive Brokers TWS API and ib_async.

## Exchange Code Table

| Exchange | Description | Instrument Types | Country |
|----------|-------------|-------------------|---------|
| `IDEALPRO` | Primary IB forex venue | Forex, CFD | Global |
| `IDEAL` | Virtual Forex (test) | Forex | Global |
| `SMART` | Smart order routing | Stocks | US/Global |
| `NYSE` | New York Stock Exchange | Stocks | US |
| `NASDAQ` | Nasdaq | Stocks | US |
| `ARCA` | NYSE Arca | Stocks | US |
| `CME` | Chicago Mercantile Exchange | Futures | US |
| `COMEX` | Commodity Exchange | Futures | US |
| `EUREX` | European Exchange | Futures | Europe |
| `LSE` | London Stock Exchange | Stocks | UK |
| `EBS` | SIX Swiss Exchange | Stocks | Switzerland |
| `SEHK` | Hong Kong Stock Exchange | Stocks | Hong Kong |

## Recommended Setup by Instrument

### Forex

```python
from ib_async import Forex

# Correct - pair should be "EURUSD" not "EUR/USD"
contract = Forex(pair="EURUSD", exchange="IDEALPRO")
```

| .env Setting | Value |
|-------------|-------|
| `INSTRUMENT_TYPE` | `FOREX` |
| `SYMBOL` | `EURUSD` |
| `EXCHANGE` | `IDEALPRO` |
| `CURRENCY` | `USD` |

### Stocks

```python
from ib_async import Stock

# With smart routing
contract = Stock(symbol="AAPL", exchange="SMART", currency="USD")

# With specific primary exchange (recommended for clarity)
contract = Stock(symbol="AAPL", exchange="SMART", currency="USD", primaryExchange="NASDAQ")
```

| .env Setting | Value |
|-------------|-------|
| `INSTRUMENT_TYPE` | `STOCK` |
| `SYMBOL` | `AAPL` |
| `EXCHANGE` | `SMART` |
| `CURRENCY` | `USD` |

### CFDs

```python
from ib_async import CFD

# Currency index CFD
contract = CFD(symbol="EUR", currency="USD", exchange="IDEALPRO")
```

| .env Setting | Value |
|-------------|-------|
| `INSTRUMENT_TYPE` | `CFD` |
| `SYMBOL` | `EUR` |
| `EXCHANGE` | `IDEALPRO` |
| `CURRENCY` | `USD` |

## Contract Qualification

**Important**: Always qualify contracts before trading:

```python
# Create contract
contract = Forex(pair="EURUSD", exchange="IDEALPRO")

# Qualify to get valid conId
qualified = ib.qualifyContracts(contract)
contract = qualified[0]  # Now has valid conId

# Trade
ib.placeOrder(contract, MarketOrder("BUY", 1000))
```

Without qualification, orders may not execute as `conId` will be 0.

## Common Issues

1. **Forex pair format**: Use `"EURUSD"` not `"EUR/USD"`
2. **Missing qualification**: Always call `ib.qualifyContracts()` before trading
3. **Stock ambiguity**: Use `primaryExchange` when multiple exchanges have same symbol
