# Trading Agents Team Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent system that covers the full algorithmic trading cycle — data ingestion, technical analysis, signal generation, risk management, order execution, and session monitoring — using Interactive Brokers via ib_async.

**Architecture:** A top-level Orchestrator agent coordinates six specialist agents in an event-driven loop. Each agent is implemented using the Claude Agent SDK with OpenRouter-assigned LLMs and exposes a set of typed tools. Agents communicate through a shared in-memory state object passed per bar tick.

**Tech Stack:** Python 3.12, claude-agent-sdk, anthropic SDK, openrouter (OpenAI-compatible base URL), ib_async, pandas, numpy, pydantic v2, uv

---

## File Map

```
trading-agents-01/
├── pyproject.toml
├── .env.example
├── src/
│   ├── config.py                        # Env config & LLM model assignments
│   ├── state.py                         # Shared TradingSessionState dataclass
│   ├── main.py                          # Entry point — wires up and runs session
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ibkr_tools.py               # ib_async wrappers: connect, data, orders
│   │   ├── analysis_tools.py           # SMA, Bollinger Bands, signal calc
│   │   └── risk_tools.py               # Position sizing, SL/TP price calc
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── market_data_agent.py        # Subscribes to bars, maintains OHLCV history
│   │   ├── analysis_agent.py           # Computes indicators, outputs signals
│   │   ├── strategy_agent.py           # Selects active strategy, manages parameters
│   │   ├── risk_agent.py               # Validates signals, sizes positions
│   │   ├── execution_agent.py          # Places/cancels orders via ib_async
│   │   ├── monitor_agent.py            # Tracks P&L, checks session end conditions
│   │   └── orchestrator.py             # Event loop, agent coordination
│   └── models/
│       ├── __init__.py
│       ├── market_data.py              # Bar, OHLCVHistory
│       ├── signals.py                  # Signal, Direction enum
│       ├── orders.py                   # OrderRequest, OrderFill
│       └── portfolio.py                # Position, SessionSummary
└── tests/
    ├── tools/
    │   ├── test_analysis_tools.py
    │   └── test_risk_tools.py
    ├── agents/
    │   ├── test_analysis_agent.py
    │   └── test_risk_agent.py
    └── conftest.py
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `src/__init__.py`, `src/tools/__init__.py`, `src/agents/__init__.py`, `src/models/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "trading-agents-01"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "anthropic>=0.40.0",
    "claude-agent-sdk>=0.1.0",
    "ib_async>=2.0.0",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "pydantic>=2.7.0",
    "python-dotenv>=1.0.0",
    "openai>=1.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Add dependencies**

```bash
uv add anthropic claude-agent-sdk ib_async pandas numpy pydantic python-dotenv openai
uv add --dev pytest pytest-asyncio pytest-mock
```

Expected: packages installed without errors.

- [ ] **Step 3: Create .env.example**

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...

# LLM model assignments per agent (OpenRouter model IDs)
MODEL_ORCHESTRATOR=anthropic/claude-sonnet-4-6
MODEL_MARKET_DATA=anthropic/claude-haiku-4-5
MODEL_ANALYSIS=anthropic/claude-sonnet-4-6
MODEL_STRATEGY=anthropic/claude-sonnet-4-6
MODEL_RISK=anthropic/claude-sonnet-4-6
MODEL_EXECUTION=anthropic/claude-haiku-4-5
MODEL_MONITOR=anthropic/claude-haiku-4-5

# IBKR connection
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# Trading session
SYMBOL=EUR/USD
EXCHANGE=IDEALPRO
CURRENCY=USD
BAR_SIZE=20 mins
SESSION_DURATION_HOURS=8
MAX_POSITION_UNITS=100000

# Risk parameters
STOP_LOSS_PCT=0.005
TAKE_PROFIT_PCT=0.010
MAX_DRAWDOWN_PCT=0.02
INITIAL_CAPITAL=10000
```

- [ ] **Step 4: Create empty __init__.py files**

```bash
touch src/__init__.py src/tools/__init__.py src/agents/__init__.py src/models/__init__.py
touch tests/__init__.py tests/tools/__init__.py tests/agents/__init__.py
```

- [ ] **Step 5: Create conftest.py**

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2024-01-01", periods=50, freq="20min", tz="UTC")
    np.random.seed(42)
    close = 1.1000 + np.cumsum(np.random.randn(50) * 0.0005)
    return pd.DataFrame({
        "open": close - 0.0002,
        "high": close + 0.0003,
        "low": close - 0.0003,
        "close": close,
        "volume": np.random.randint(100, 1000, 50).astype(float),
    }, index=dates)
```

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml .env.example src/ tests/
git commit -m "feat: project bootstrap with deps and structure"
```

---

## Task 2: Data Models

**Files:**
- Create: `src/models/market_data.py`
- Create: `src/models/signals.py`
- Create: `src/models/orders.py`
- Create: `src/models/portfolio.py`

- [ ] **Step 1: Write test for Bar and OHLCVHistory**

```python
# tests/test_models_market_data.py
from src.models.market_data import Bar, OHLCVHistory
from datetime import datetime, timezone

def test_bar_creation():
    bar = Bar(
        timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
        open=1.1000, high=1.1010, low=1.0990, close=1.1005, volume=500
    )
    assert bar.close == 1.1005

def test_ohlcv_history_append_and_dataframe(sample_ohlcv):
    history = OHLCVHistory(max_bars=100)
    for ts, row in sample_ohlcv.iterrows():
        history.append(Bar(timestamp=ts, open=row.open, high=row.high,
                           low=row.low, close=row.close, volume=row.volume))
    df = history.to_dataframe()
    assert len(df) == 50
    assert "close" in df.columns

def test_ohlcv_history_max_bars():
    history = OHLCVHistory(max_bars=5)
    for i in range(10):
        history.append(Bar(
            timestamp=datetime(2024, 1, 1, i, 0, tzinfo=timezone.utc),
            open=1.1, high=1.11, low=1.09, close=1.10, volume=100
        ))
    assert len(history.bars) == 5
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_models_market_data.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement market_data.py**

```python
# src/models/market_data.py
from __future__ import annotations
from collections import deque
from datetime import datetime
from pydantic import BaseModel
import pandas as pd

class Bar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class OHLCVHistory:
    def __init__(self, max_bars: int = 500):
        self.bars: deque[Bar] = deque(maxlen=max_bars)

    def append(self, bar: Bar) -> None:
        self.bars.append(bar)

    def to_dataframe(self) -> pd.DataFrame:
        if not self.bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        return pd.DataFrame(
            [b.model_dump() for b in self.bars]
        ).set_index("timestamp")
```

- [ ] **Step 4: Implement signals.py**

```python
# src/models/signals.py
from enum import Enum
from pydantic import BaseModel

class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

class Signal(BaseModel):
    direction: Direction
    strategy: str
    confidence: float = 1.0
    reason: str = ""
```

- [ ] **Step 5: Implement orders.py**

```python
# src/models/orders.py
from datetime import datetime
from pydantic import BaseModel

class OrderRequest(BaseModel):
    symbol: str
    action: str          # "BUY" or "SELL"
    quantity: float
    order_type: str = "MKT"
    stop_loss: float | None = None
    take_profit: float | None = None

class OrderFill(BaseModel):
    order_id: int
    symbol: str
    action: str
    quantity: float
    fill_price: float
    timestamp: datetime
```

- [ ] **Step 6: Implement portfolio.py**

```python
# src/models/portfolio.py
from datetime import datetime
from pydantic import BaseModel

class Position(BaseModel):
    symbol: str
    quantity: float       # positive = long, negative = short
    avg_cost: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

class SessionSummary(BaseModel):
    start_time: datetime
    end_time: datetime
    total_trades: int
    realized_pnl: float
    max_drawdown: float
    final_position: float
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_models_market_data.py -v
```
Expected: 3 PASSED

- [ ] **Step 8: Commit**

```bash
git add src/models/ tests/test_models_market_data.py
git commit -m "feat: add data models (Bar, Signal, OrderRequest, Position)"
```

---

## Task 3: Shared Session State

**Files:**
- Create: `src/state.py`

- [ ] **Step 1: Write test**

```python
# tests/test_state.py
from src.state import TradingSessionState
from src.models.signals import Signal, Direction

def test_state_default_values():
    state = TradingSessionState(symbol="EUR/USD")
    assert state.current_position == 0.0
    assert state.active_signal is None
    assert state.session_active is False

def test_state_update_signal():
    state = TradingSessionState(symbol="EUR/USD")
    sig = Signal(direction=Direction.LONG, strategy="SMA", reason="SMA crossover")
    state.active_signal = sig
    assert state.active_signal.direction == Direction.LONG
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_state.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement state.py**

```python
# src/state.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_state.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/state.py tests/test_state.py
git commit -m "feat: add TradingSessionState shared state container"
```

---

## Task 4: Config Module

**Files:**
- Create: `src/config.py`

- [ ] **Step 1: Implement config.py**

```python
# src/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    anthropic_api_key: str
    openrouter_api_key: str
    model_orchestrator: str
    model_market_data: str
    model_analysis: str
    model_strategy: str
    model_risk: str
    model_execution: str
    model_monitor: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    symbol: str
    exchange: str
    currency: str
    bar_size: str
    session_duration_hours: float
    max_position_units: float
    stop_loss_pct: float
    take_profit_pct: float
    max_drawdown_pct: float
    initial_capital: float

def load_config() -> Config:
    return Config(
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
        model_orchestrator=os.getenv("MODEL_ORCHESTRATOR", "anthropic/claude-sonnet-4-6"),
        model_market_data=os.getenv("MODEL_MARKET_DATA", "anthropic/claude-haiku-4-5"),
        model_analysis=os.getenv("MODEL_ANALYSIS", "anthropic/claude-sonnet-4-6"),
        model_strategy=os.getenv("MODEL_STRATEGY", "anthropic/claude-sonnet-4-6"),
        model_risk=os.getenv("MODEL_RISK", "anthropic/claude-sonnet-4-6"),
        model_execution=os.getenv("MODEL_EXECUTION", "anthropic/claude-haiku-4-5"),
        model_monitor=os.getenv("MODEL_MONITOR", "anthropic/claude-haiku-4-5"),
        ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
        ibkr_port=int(os.getenv("IBKR_PORT", "7497")),
        ibkr_client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        symbol=os.getenv("SYMBOL", "EUR/USD"),
        exchange=os.getenv("EXCHANGE", "IDEALPRO"),
        currency=os.getenv("CURRENCY", "USD"),
        bar_size=os.getenv("BAR_SIZE", "20 mins"),
        session_duration_hours=float(os.getenv("SESSION_DURATION_HOURS", "8")),
        max_position_units=float(os.getenv("MAX_POSITION_UNITS", "100000")),
        stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.005")),
        take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.010")),
        max_drawdown_pct=float(os.getenv("MAX_DRAWDOWN_PCT", "0.02")),
        initial_capital=float(os.getenv("INITIAL_CAPITAL", "10000")),
    )
```

- [ ] **Step 2: Commit**

```bash
git add src/config.py
git commit -m "feat: add Config loader from environment variables"
```

---

## Task 5: Analysis Tools

**Files:**
- Create: `src/tools/analysis_tools.py`
- Create: `tests/tools/test_analysis_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/tools/test_analysis_tools.py
import pytest
import pandas as pd
from src.tools.analysis_tools import (
    compute_sma, compute_bollinger_bands, sma_signal, mean_reversion_signal
)
from src.models.signals import Direction

def test_compute_sma(sample_ohlcv):
    result = compute_sma(sample_ohlcv, short=5, long=20)
    assert "sma_short" in result.columns
    assert "sma_long" in result.columns
    assert result["sma_short"].iloc[-1] == pytest.approx(
        sample_ohlcv["close"].iloc[-5:].mean(), rel=1e-5
    )

def test_compute_bollinger_bands(sample_ohlcv):
    result = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    assert "sma" in result.columns
    assert "upper" in result.columns
    assert "lower" in result.columns
    last = result.iloc[-1]
    assert last["upper"] > last["sma"] > last["lower"]

def test_sma_signal_long(sample_ohlcv):
    df = compute_sma(sample_ohlcv, short=5, long=20)
    df.loc[df.index[-1], "sma_short"] = df.loc[df.index[-1], "sma_long"] + 0.001
    signal = sma_signal(df)
    assert signal.direction == Direction.LONG
    assert signal.strategy == "SMA"

def test_sma_signal_short(sample_ohlcv):
    df = compute_sma(sample_ohlcv, short=5, long=20)
    df.loc[df.index[-1], "sma_short"] = df.loc[df.index[-1], "sma_long"] - 0.001
    signal = sma_signal(df)
    assert signal.direction == Direction.SHORT

def test_mean_reversion_signal_long(sample_ohlcv):
    df = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    df.loc[df.index[-1], "close"] = df.loc[df.index[-1], "lower"] - 0.001
    signal = mean_reversion_signal(df)
    assert signal.direction == Direction.LONG
    assert signal.strategy == "MeanReversion"

def test_mean_reversion_signal_flat(sample_ohlcv):
    df = compute_bollinger_bands(sample_ohlcv, window=20, dev=2.0)
    mid = (df.iloc[-1]["upper"] + df.iloc[-1]["lower"]) / 2
    df.loc[df.index[-1], "close"] = mid
    signal = mean_reversion_signal(df)
    assert signal.direction == Direction.FLAT
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/tools/test_analysis_tools.py -v
```
Expected: all FAILED with ModuleNotFoundError

- [ ] **Step 3: Implement analysis_tools.py**

```python
# src/tools/analysis_tools.py
import numpy as np
import pandas as pd
from src.models.signals import Signal, Direction

def compute_sma(df: pd.DataFrame, short: int = 10, long: int = 50) -> pd.DataFrame:
    out = df.copy()
    out["sma_short"] = out["close"].rolling(short).mean()
    out["sma_long"] = out["close"].rolling(long).mean()
    return out

def compute_bollinger_bands(df: pd.DataFrame, window: int = 20, dev: float = 2.0) -> pd.DataFrame:
    out = df.copy()
    out["sma"] = out["close"].rolling(window).mean()
    std = out["close"].rolling(window).std()
    out["upper"] = out["sma"] + dev * std
    out["lower"] = out["sma"] - dev * std
    out["distance"] = out["close"] - out["sma"]
    return out

def sma_signal(df: pd.DataFrame) -> Signal:
    last = df.iloc[-1]
    if pd.isna(last["sma_short"]) or pd.isna(last["sma_long"]):
        return Signal(direction=Direction.FLAT, strategy="SMA", reason="insufficient data")
    if last["sma_short"] > last["sma_long"]:
        return Signal(direction=Direction.LONG, strategy="SMA",
                      reason=f"SMA_S {last['sma_short']:.5f} > SMA_L {last['sma_long']:.5f}")
    return Signal(direction=Direction.SHORT, strategy="SMA",
                  reason=f"SMA_S {last['sma_short']:.5f} < SMA_L {last['sma_long']:.5f}")

def mean_reversion_signal(df: pd.DataFrame) -> Signal:
    last = df.iloc[-1]
    if pd.isna(last.get("upper", float("nan"))):
        return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                      reason="insufficient data")
    if last["close"] < last["lower"]:
        return Signal(direction=Direction.LONG, strategy="MeanReversion",
                      reason=f"price {last['close']:.5f} below lower band {last['lower']:.5f}")
    if last["close"] > last["upper"]:
        return Signal(direction=Direction.SHORT, strategy="MeanReversion",
                      reason=f"price {last['close']:.5f} above upper band {last['upper']:.5f}")
    prev = df.iloc[-2] if len(df) > 1 else None
    if prev is not None and (last["distance"] * prev["distance"] < 0):
        return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                      reason="price crossed SMA — closing position")
    return Signal(direction=Direction.FLAT, strategy="MeanReversion",
                  reason="price within bands")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/tools/test_analysis_tools.py -v
```
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/tools/analysis_tools.py tests/tools/test_analysis_tools.py
git commit -m "feat: add SMA and Bollinger Band analysis tools with tests"
```

---

## Task 6: Risk Tools

**Files:**
- Create: `src/tools/risk_tools.py`
- Create: `tests/tools/test_risk_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/tools/test_risk_tools.py
import pytest
from src.tools.risk_tools import (
    compute_stop_loss_price, compute_take_profit_price,
    compute_position_size, check_max_drawdown,
)
from src.models.signals import Direction

def test_stop_loss_long():
    price = compute_stop_loss_price(entry=1.1000, direction=Direction.LONG, sl_pct=0.005)
    assert price == pytest.approx(1.1000 * (1 - 0.005), rel=1e-5)

def test_stop_loss_short():
    price = compute_stop_loss_price(entry=1.1000, direction=Direction.SHORT, sl_pct=0.005)
    assert price == pytest.approx(1.1000 * (1 + 0.005), rel=1e-5)

def test_take_profit_long():
    price = compute_take_profit_price(entry=1.1000, direction=Direction.LONG, tp_pct=0.010)
    assert price == pytest.approx(1.1000 * (1 + 0.010), rel=1e-5)

def test_take_profit_short():
    price = compute_take_profit_price(entry=1.1000, direction=Direction.SHORT, tp_pct=0.010)
    assert price == pytest.approx(1.1000 * (1 - 0.010), rel=1e-5)

def test_position_size_long():
    size = compute_position_size(max_units=100000, direction=Direction.LONG)
    assert size == 100000

def test_position_size_short():
    size = compute_position_size(max_units=100000, direction=Direction.SHORT)
    assert size == -100000

def test_position_size_flat():
    size = compute_position_size(max_units=100000, direction=Direction.FLAT)
    assert size == 0

def test_check_max_drawdown_ok():
    result = check_max_drawdown(realized_pnl=-100, initial_capital=10000, max_dd_pct=0.02)
    assert result is True

def test_check_max_drawdown_breached():
    result = check_max_drawdown(realized_pnl=-250, initial_capital=10000, max_dd_pct=0.02)
    assert result is False
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/tools/test_risk_tools.py -v
```
Expected: all FAILED

- [ ] **Step 3: Implement risk_tools.py**

```python
# src/tools/risk_tools.py
from src.models.signals import Direction

def compute_stop_loss_price(entry: float, direction: Direction, sl_pct: float) -> float:
    if direction == Direction.LONG:
        return round(entry * (1 - sl_pct), 5)
    return round(entry * (1 + sl_pct), 5)

def compute_take_profit_price(entry: float, direction: Direction, tp_pct: float) -> float:
    if direction == Direction.LONG:
        return round(entry * (1 + tp_pct), 5)
    return round(entry * (1 - tp_pct), 5)

def compute_position_size(max_units: float, direction: Direction) -> float:
    if direction == Direction.LONG:
        return max_units
    if direction == Direction.SHORT:
        return -max_units
    return 0.0

def check_max_drawdown(realized_pnl: float, initial_capital: float, max_dd_pct: float) -> bool:
    """Returns True if within acceptable drawdown, False if limit breached."""
    drawdown = abs(min(realized_pnl, 0)) / initial_capital
    return drawdown <= max_dd_pct
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/tools/test_risk_tools.py -v
```
Expected: 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/tools/risk_tools.py tests/tools/test_risk_tools.py
git commit -m "feat: add risk tools (SL/TP calc, position sizing, drawdown check)"
```

---

## Task 7: IBKR Tools

**Files:**
- Create: `src/tools/ibkr_tools.py`
- Create: `tests/tools/test_ibkr_tools.py`

Note: These tools wrap ib_async. Unit tests mock `IB`. Integration tests require a live TWS/Gateway.

- [ ] **Step 1: Write unit test with mock**

```python
# tests/tools/test_ibkr_tools.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.ibkr_tools import IBKRClient

@pytest.fixture
def mock_ib():
    ib = MagicMock()
    ib.connectAsync = AsyncMock()
    ib.disconnect = MagicMock()
    ib.positions = MagicMock(return_value=[])
    ib.placeOrder = MagicMock(return_value=MagicMock(orderId=42))
    return ib

async def test_get_position_empty(mock_ib):
    client = IBKRClient(host="127.0.0.1", port=7497, client_id=1)
    client.ib = mock_ib
    pos = client.get_position("EUR")
    assert pos == 0.0
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/tools/test_ibkr_tools.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement ibkr_tools.py**

```python
# src/tools/ibkr_tools.py
from __future__ import annotations
from datetime import datetime, timezone
from ib_async import IB, Forex, BarData, MarketOrder, StopOrder, LimitOrder, Trade
from src.models.market_data import Bar

class IBKRClient:
    def __init__(self, host: str, port: int, client_id: int):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()

    async def connect(self) -> None:
        await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)

    def disconnect(self) -> None:
        self.ib.disconnect()

    def make_forex_contract(self, symbol: str, currency: str, exchange: str) -> Forex:
        pair, base = symbol.split("/")
        return Forex(pair=pair + base, exchange=exchange)

    def get_position(self, symbol: str) -> float:
        for pos in self.ib.positions():
            if symbol in pos.contract.localSymbol:
                return pos.position
        return 0.0

    def get_current_price(self, contract) -> float:
        ticker = self.ib.ticker(contract)
        if ticker and ticker.last:
            return float(ticker.last)
        if ticker and ticker.midpoint():
            return float(ticker.midpoint())
        return 0.0

    async def request_historical_bars(
        self, contract, bar_size: str = "20 mins", duration: str = "2 D"
    ) -> list[Bar]:
        bars: list[BarData] = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT",
            useRTH=False,
        )
        return [
            Bar(
                timestamp=b.date.replace(tzinfo=timezone.utc)
                    if hasattr(b.date, "replace") else datetime.now(tz=timezone.utc),
                open=b.open, high=b.high, low=b.low,
                close=b.close, volume=float(b.volume),
            )
            for b in bars
        ]

    def place_bracket_order(
        self,
        contract,
        action: str,
        quantity: float,
        stop_loss: float,
        take_profit: float,
    ) -> list[Trade]:
        parent = MarketOrder(action, quantity)
        parent.transmit = False

        sl_action = "SELL" if action == "BUY" else "BUY"
        stop = StopOrder(sl_action, quantity, stop_loss)
        stop.parentId = parent.orderId
        stop.transmit = False

        tp = LimitOrder(sl_action, quantity, take_profit)
        tp.parentId = parent.orderId
        tp.transmit = True

        return [
            self.ib.placeOrder(contract, parent),
            self.ib.placeOrder(contract, stop),
            self.ib.placeOrder(contract, tp),
        ]

    def cancel_all_orders(self, contract) -> None:
        for trade in self.ib.openTrades():
            if trade.contract.conId == contract.conId:
                self.ib.cancelOrder(trade.order)
```

- [ ] **Step 4: Run test**

```bash
pytest tests/tools/test_ibkr_tools.py -v
```
Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add src/tools/ibkr_tools.py tests/tools/test_ibkr_tools.py
git commit -m "feat: add IBKRClient wrapper for ib_async (connect, data, orders)"
```

---

## Task 8: Market Data Agent

**Files:**
- Create: `src/agents/market_data_agent.py`
- Create: `tests/agents/test_market_data_agent.py`

- [ ] **Step 1: Write test**

```python
# tests/agents/test_market_data_agent.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.agents.market_data_agent import MarketDataAgent
from src.state import TradingSessionState
from src.models.market_data import Bar
from datetime import datetime, timezone

@pytest.fixture
def state():
    return TradingSessionState(symbol="EUR/USD")

@pytest.fixture
def mock_client():
    client = MagicMock()
    bar = Bar(timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
              open=1.1, high=1.11, low=1.09, close=1.105, volume=500)
    client.request_historical_bars = AsyncMock(return_value=[bar])
    return client

async def test_load_history_populates_state(state, mock_client):
    agent = MarketDataAgent(client=mock_client)
    await agent.load_history(state, contract=MagicMock(), bar_size="20 mins")
    assert len(state.history.bars) == 1
    assert state.history.bars[0].close == 1.105

def test_on_bar_update_appends_bar(state, mock_client):
    agent = MarketDataAgent(client=mock_client)
    bar = Bar(timestamp=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
              open=1.11, high=1.12, low=1.10, close=1.115, volume=300)
    agent.on_bar_update(state, bar)
    assert len(state.history.bars) == 1
    assert state.current_price == pytest.approx(1.115)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_market_data_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement market_data_agent.py**

```python
# src/agents/market_data_agent.py
from __future__ import annotations
from src.state import TradingSessionState
from src.tools.ibkr_tools import IBKRClient
from src.models.market_data import Bar

class MarketDataAgent:
    """Loads historical bars and processes real-time bar updates into session state."""

    def __init__(self, client: IBKRClient):
        self.client = client

    async def load_history(
        self, state: TradingSessionState, contract, bar_size: str, duration: str = "2 D"
    ) -> None:
        bars = await self.client.request_historical_bars(contract, bar_size, duration)
        for bar in bars:
            state.history.append(bar)

    def on_bar_update(self, state: TradingSessionState, bar: Bar) -> None:
        state.history.append(bar)
        state.current_price = bar.close
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_market_data_agent.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/market_data_agent.py tests/agents/test_market_data_agent.py
git commit -m "feat: add MarketDataAgent for history loading and bar updates"
```

---

## Task 9: Analysis Agent

**Files:**
- Create: `src/agents/analysis_agent.py`
- Create: `tests/agents/test_analysis_agent.py`

The Analysis Agent calls an LLM via OpenRouter to interpret indicator values and emit a trading signal.

- [ ] **Step 1: Write test**

```python
# tests/agents/test_analysis_agent.py
import pytest
from unittest.mock import patch
from src.agents.analysis_agent import AnalysisAgent
from src.state import TradingSessionState
from src.models.signals import Direction

@pytest.fixture
def state_with_data(sample_ohlcv):
    from src.models.market_data import Bar
    state = TradingSessionState(symbol="EUR/USD")
    for ts, row in sample_ohlcv.iterrows():
        state.history.append(Bar(timestamp=ts, open=row.open, high=row.high,
                                 low=row.low, close=row.close, volume=row.volume))
    state.current_price = float(sample_ohlcv["close"].iloc[-1])
    return state

def test_run_returns_long_signal(state_with_data):
    with patch("src.agents.analysis_agent.call_llm") as mock_llm:
        mock_llm.return_value = {"direction": "long", "strategy": "SMA", "reason": "test"}
        agent = AnalysisAgent(model="anthropic/claude-haiku-4-5", api_key="test")
        signal = agent.run(state_with_data, strategy="SMA", sma_short=5, sma_long=20)
        assert signal.direction == Direction.LONG

def test_run_falls_back_on_llm_error(state_with_data):
    with patch("src.agents.analysis_agent.call_llm", side_effect=Exception("LLM error")):
        agent = AnalysisAgent(model="anthropic/claude-haiku-4-5", api_key="test")
        signal = agent.run(state_with_data, strategy="SMA", sma_short=5, sma_long=20)
        assert signal.direction in (Direction.LONG, Direction.SHORT, Direction.FLAT)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_analysis_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement analysis_agent.py**

```python
# src/agents/analysis_agent.py
from __future__ import annotations
import json
from openai import OpenAI
from src.state import TradingSessionState
from src.models.signals import Signal, Direction
from src.tools.analysis_tools import (
    compute_sma, compute_bollinger_bands, sma_signal, mean_reversion_signal
)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are a technical analysis agent for algorithmic trading.
You receive computed indicator values and decide the trading signal.
Always respond with a JSON object: {"direction": "long"|"short"|"flat", "strategy": str, "reason": str}
Base your decision strictly on the indicators provided."""

def call_llm(model: str, api_key: str, user_message: str) -> dict:
    client = OpenAI(base_url=OPENROUTER_BASE, api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

class AnalysisAgent:
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    def run(
        self,
        state: TradingSessionState,
        strategy: str = "SMA",
        sma_short: int = 10,
        sma_long: int = 50,
        bb_window: int = 20,
        bb_dev: float = 2.0,
    ) -> Signal:
        df = state.history.to_dataframe()
        if len(df) < max(sma_long, bb_window) + 2:
            return Signal(direction=Direction.FLAT, strategy=strategy,
                          reason="insufficient data")

        if strategy == "SMA":
            df = compute_sma(df, short=sma_short, long=sma_long)
            fallback = sma_signal(df)
            last = df.iloc[-1]
            user_msg = (
                f"Strategy: SMA crossover\n"
                f"Current price: {state.current_price:.5f}\n"
                f"SMA({sma_short}): {last['sma_short']:.5f}\n"
                f"SMA({sma_long}): {last['sma_long']:.5f}\n"
                f"Previous SMA({sma_short}): {df.iloc[-2]['sma_short']:.5f}\n"
                f"Suggest a trading signal."
            )
        else:
            df = compute_bollinger_bands(df, window=bb_window, dev=bb_dev)
            fallback = mean_reversion_signal(df)
            last = df.iloc[-1]
            user_msg = (
                f"Strategy: Mean Reversion (Bollinger Bands)\n"
                f"Current price: {state.current_price:.5f}\n"
                f"SMA({bb_window}): {last['sma']:.5f}\n"
                f"Upper band: {last['upper']:.5f}\n"
                f"Lower band: {last['lower']:.5f}\n"
                f"Distance from SMA: {last['distance']:.5f}\n"
                f"Suggest a trading signal."
            )

        try:
            result = call_llm(self.model, self.api_key, user_msg)
            return Signal(
                direction=Direction(result["direction"]),
                strategy=result.get("strategy", strategy),
                reason=result.get("reason", ""),
            )
        except Exception:
            return fallback
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_analysis_agent.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/analysis_agent.py tests/agents/test_analysis_agent.py
git commit -m "feat: add AnalysisAgent with LLM-driven indicator interpretation"
```

---

## Task 10: Strategy Agent

**Files:**
- Create: `src/agents/strategy_agent.py`
- Create: `tests/agents/test_strategy_agent.py`

- [ ] **Step 1: Write test**

```python
# tests/agents/test_strategy_agent.py
import pytest
from unittest.mock import patch
from src.agents.strategy_agent import StrategyAgent
from src.state import TradingSessionState

@pytest.fixture
def state_with_data(sample_ohlcv):
    from src.models.market_data import Bar
    state = TradingSessionState(symbol="EUR/USD")
    for ts, row in sample_ohlcv.iterrows():
        state.history.append(Bar(timestamp=ts, open=row.open, high=row.high,
                                 low=row.low, close=row.close, volume=row.volume))
    return state

def test_select_strategy_returns_valid_name(state_with_data):
    with patch("src.agents.strategy_agent.call_llm") as mock_llm:
        mock_llm.return_value = {"strategy": "SMA", "reason": "trending market"}
        agent = StrategyAgent(model="test-model", api_key="test")
        strategy = agent.select_strategy(state_with_data)
        assert strategy in ("SMA", "MeanReversion")

def test_select_strategy_falls_back_on_error(state_with_data):
    with patch("src.agents.strategy_agent.call_llm", side_effect=Exception("error")):
        agent = StrategyAgent(model="test-model", api_key="test")
        strategy = agent.select_strategy(state_with_data)
        assert strategy == "SMA"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_strategy_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement strategy_agent.py**

```python
# src/agents/strategy_agent.py
from __future__ import annotations
import json
import numpy as np
from openai import OpenAI
from src.state import TradingSessionState

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are a trading strategy selection agent.
Given market statistics, choose the best strategy.
Respond with JSON: {"strategy": "SMA"|"MeanReversion", "reason": str}
- SMA crossover works in trending markets (low autocorrelation, directional momentum).
- MeanReversion (Bollinger Bands) works in ranging/choppy markets (high autocorrelation)."""

def call_llm(model: str, api_key: str, message: str) -> dict:
    client = OpenAI(base_url=OPENROUTER_BASE, api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

class StrategyAgent:
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    def select_strategy(self, state: TradingSessionState) -> str:
        df = state.history.to_dataframe()
        if len(df) < 20:
            return "SMA"

        returns = df["close"].pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252 * 26))
        autocorr = float(returns.autocorr(lag=1))
        trend_strength = (
            abs(float(returns.rolling(20).mean().iloc[-1])) / float(returns.std())
        )

        msg = (
            f"Annualized volatility: {volatility:.4f}\n"
            f"Returns autocorrelation (lag-1): {autocorr:.4f}\n"
            f"Trend strength (|mean|/std, 20-bar): {trend_strength:.4f}\n"
            f"Number of bars: {len(df)}\n"
            f"Select the best strategy."
        )
        try:
            result = call_llm(self.model, self.api_key, msg)
            strategy = result.get("strategy", "SMA")
            return strategy if strategy in ("SMA", "MeanReversion") else "SMA"
        except Exception:
            return "SMA"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_strategy_agent.py -v
```
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/strategy_agent.py tests/agents/test_strategy_agent.py
git commit -m "feat: add StrategyAgent for LLM-driven strategy selection"
```

---

## Task 11: Risk Agent

**Files:**
- Create: `src/agents/risk_agent.py`
- Create: `tests/agents/test_risk_agent.py`

- [ ] **Step 1: Write test**

```python
# tests/agents/test_risk_agent.py
import pytest
from src.agents.risk_agent import RiskAgent, RiskDecision
from src.state import TradingSessionState
from src.models.signals import Signal, Direction

@pytest.fixture
def state():
    s = TradingSessionState(symbol="EUR/USD")
    s.current_price = 1.1000
    s.realized_pnl = 0.0
    return s

def test_approve_long_signal(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    signal = Signal(direction=Direction.LONG, strategy="SMA", reason="test")
    result = agent.evaluate(state, signal)
    assert result.approved is True
    assert result.quantity == 100000
    assert result.stop_loss == pytest.approx(1.1000 * 0.995, rel=1e-5)
    assert result.take_profit == pytest.approx(1.1000 * 1.010, rel=1e-5)

def test_reject_when_drawdown_exceeded(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    state.realized_pnl = -300.0
    signal = Signal(direction=Direction.LONG, strategy="SMA", reason="test")
    result = agent.evaluate(state, signal)
    assert result.approved is False
    assert "drawdown" in result.reason.lower()

def test_flat_signal_always_approved(state):
    agent = RiskAgent(max_units=100000, sl_pct=0.005, tp_pct=0.010,
                      max_drawdown_pct=0.02, initial_capital=10000)
    signal = Signal(direction=Direction.FLAT, strategy="SMA", reason="no signal")
    result = agent.evaluate(state, signal)
    assert result.approved is True
    assert result.quantity == 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_risk_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement risk_agent.py**

```python
# src/agents/risk_agent.py
from __future__ import annotations
from dataclasses import dataclass
from src.state import TradingSessionState
from src.models.signals import Signal, Direction
from src.tools.risk_tools import (
    compute_stop_loss_price, compute_take_profit_price,
    compute_position_size, check_max_drawdown,
)

@dataclass
class RiskDecision:
    approved: bool
    quantity: float
    stop_loss: float | None
    take_profit: float | None
    reason: str

class RiskAgent:
    def __init__(
        self,
        max_units: float,
        sl_pct: float,
        tp_pct: float,
        max_drawdown_pct: float,
        initial_capital: float = 10000.0,
    ):
        self.max_units = max_units
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.initial_capital = initial_capital

    def evaluate(self, state: TradingSessionState, signal: Signal) -> RiskDecision:
        if signal.direction == Direction.FLAT:
            return RiskDecision(approved=True, quantity=0, stop_loss=None,
                                take_profit=None, reason="flat signal")

        if not check_max_drawdown(state.realized_pnl, self.initial_capital, self.max_drawdown_pct):
            return RiskDecision(
                approved=False, quantity=0, stop_loss=None, take_profit=None,
                reason=f"max drawdown exceeded: pnl={state.realized_pnl:.2f}",
            )

        entry = state.current_price
        sl = compute_stop_loss_price(entry, signal.direction, self.sl_pct)
        tp = compute_take_profit_price(entry, signal.direction, self.tp_pct)
        qty = compute_position_size(self.max_units, signal.direction)

        return RiskDecision(
            approved=True, quantity=qty, stop_loss=sl, take_profit=tp,
            reason=f"approved: qty={qty}, sl={sl:.5f}, tp={tp:.5f}",
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_risk_agent.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/risk_agent.py tests/agents/test_risk_agent.py
git commit -m "feat: add RiskAgent for position sizing and drawdown enforcement"
```

---

## Task 12: Execution Agent

**Files:**
- Create: `src/agents/execution_agent.py`
- Create: `tests/agents/test_execution_agent.py`

- [ ] **Step 1: Write test**

```python
# tests/agents/test_execution_agent.py
import pytest
from unittest.mock import MagicMock
from src.agents.execution_agent import ExecutionAgent
from src.agents.risk_agent import RiskDecision
from src.state import TradingSessionState
from src.models.signals import Direction

@pytest.fixture
def mock_client():
    c = MagicMock()
    c.get_position.return_value = 0.0
    c.place_bracket_order.return_value = [MagicMock()]
    c.cancel_all_orders = MagicMock()
    c.ib = MagicMock()
    return c

@pytest.fixture
def state():
    s = TradingSessionState(symbol="EUR/USD")
    s.current_price = 1.1000
    s.current_position = 0.0
    return s

def test_execute_long_when_flat(mock_client, state):
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=True, quantity=100000,
                            stop_loss=1.0945, take_profit=1.1110, reason="ok")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.LONG)
    mock_client.place_bracket_order.assert_called_once()
    assert state.current_position == 100000

def test_no_action_when_not_approved(mock_client, state):
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=False, quantity=0,
                            stop_loss=None, take_profit=None, reason="drawdown")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.FLAT)
    mock_client.place_bracket_order.assert_not_called()

def test_close_position_on_flat_signal(mock_client, state):
    state.current_position = 100000
    agent = ExecutionAgent(client=mock_client)
    decision = RiskDecision(approved=True, quantity=0,
                            stop_loss=None, take_profit=None, reason="flat")
    agent.execute(state, decision, contract=MagicMock(), direction=Direction.FLAT)
    mock_client.cancel_all_orders.assert_called_once()
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_execution_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement execution_agent.py**

```python
# src/agents/execution_agent.py
from __future__ import annotations
import logging
from ib_async import MarketOrder
from src.state import TradingSessionState
from src.agents.risk_agent import RiskDecision
from src.tools.ibkr_tools import IBKRClient
from src.models.signals import Direction

logger = logging.getLogger(__name__)

class ExecutionAgent:
    def __init__(self, client: IBKRClient):
        self.client = client

    def execute(
        self,
        state: TradingSessionState,
        decision: RiskDecision,
        contract,
        direction: Direction,
    ) -> None:
        if not decision.approved:
            logger.warning("Risk rejected: %s", decision.reason)
            return

        target = (
            decision.quantity if direction == Direction.LONG
            else -decision.quantity if direction == Direction.SHORT
            else 0.0
        )

        if target == state.current_position:
            return

        if target == 0 and state.current_position != 0:
            self.client.cancel_all_orders(contract)
            close_action = "SELL" if state.current_position > 0 else "BUY"
            qty = abs(state.current_position)
            self.client.ib.placeOrder(contract, MarketOrder(close_action, qty))
            state.current_position = 0.0
            logger.info("Closed position: %s %s", close_action, qty)
            return

        action = "BUY" if target > 0 else "SELL"
        qty = abs(target - state.current_position)

        if decision.stop_loss and decision.take_profit:
            self.client.place_bracket_order(
                contract, action, qty, decision.stop_loss, decision.take_profit
            )
        else:
            self.client.ib.placeOrder(contract, MarketOrder(action, qty))

        state.current_position = float(target)
        logger.info("Executed %s %s | SL=%s TP=%s",
                    action, qty, decision.stop_loss, decision.take_profit)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_execution_agent.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/execution_agent.py tests/agents/test_execution_agent.py
git commit -m "feat: add ExecutionAgent with bracket order and position management"
```

---

## Task 13: Monitor Agent

**Files:**
- Create: `src/agents/monitor_agent.py`
- Create: `tests/agents/test_monitor_agent.py`

- [ ] **Step 1: Write test**

```python
# tests/agents/test_monitor_agent.py
import pytest
from datetime import datetime, timezone
from src.agents.monitor_agent import MonitorAgent, MonitorResult
from src.state import TradingSessionState

@pytest.fixture
def active_state():
    s = TradingSessionState(symbol="EUR/USD")
    s.session_active = True
    s.session_start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    s.session_end = datetime(2024, 1, 1, 17, 0, tzinfo=timezone.utc)
    s.realized_pnl = 0.0
    return s

def test_session_healthy_mid_session(active_state):
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    assert result.should_stop is False

def test_session_stops_at_end_time(active_state):
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 17, 1, tzinfo=timezone.utc))
    assert result.should_stop is True
    assert "session end" in result.reason.lower()

def test_stops_on_drawdown_breach(active_state):
    active_state.realized_pnl = -300.0
    agent = MonitorAgent(initial_capital=10000, max_drawdown_pct=0.02)
    result = agent.check(active_state, now=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc))
    assert result.should_stop is True
    assert "drawdown" in result.reason.lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_monitor_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement monitor_agent.py**

```python
# src/agents/monitor_agent.py
from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from src.state import TradingSessionState
from src.tools.risk_tools import check_max_drawdown
from src.models.portfolio import SessionSummary

logger = logging.getLogger(__name__)

@dataclass
class MonitorResult:
    should_stop: bool
    reason: str

class MonitorAgent:
    def __init__(self, initial_capital: float, max_drawdown_pct: float):
        self.initial_capital = initial_capital
        self.max_drawdown_pct = max_drawdown_pct

    def check(self, state: TradingSessionState, now: datetime | None = None) -> MonitorResult:
        now = now or datetime.now(tz=timezone.utc)

        if state.session_end and now >= state.session_end:
            return MonitorResult(should_stop=True, reason="session end time reached")

        if not check_max_drawdown(state.realized_pnl, self.initial_capital, self.max_drawdown_pct):
            return MonitorResult(should_stop=True,
                                 reason=f"max drawdown exceeded: pnl={state.realized_pnl:.2f}")

        if state.stop_triggered:
            return MonitorResult(should_stop=True, reason="stop-loss/take-profit event received")

        return MonitorResult(should_stop=False, reason="session healthy")

    def build_summary(self, state: TradingSessionState) -> SessionSummary:
        return SessionSummary(
            start_time=state.session_start or datetime.now(tz=timezone.utc),
            end_time=datetime.now(tz=timezone.utc),
            total_trades=len(state.fills),
            realized_pnl=state.realized_pnl,
            max_drawdown=abs(min(state.realized_pnl, 0)) / self.initial_capital,
            final_position=state.current_position,
        )

    def print_summary(self, summary: SessionSummary) -> None:
        print("\n" + "=" * 50)
        print("SESSION SUMMARY")
        print(f"  Start:          {summary.start_time}")
        print(f"  End:            {summary.end_time}")
        print(f"  Total trades:   {summary.total_trades}")
        print(f"  Realized P&L:   {summary.realized_pnl:.2f}")
        print(f"  Max drawdown:   {summary.max_drawdown:.2%}")
        print(f"  Final position: {summary.final_position}")
        print("=" * 50)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_monitor_agent.py -v
```
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/monitor_agent.py tests/agents/test_monitor_agent.py
git commit -m "feat: add MonitorAgent for session lifecycle and drawdown tracking"
```

---

## Task 14: Backtesting Agent

**Files:**
- Create: `src/agents/backtest_agent.py`
- Create: `tests/agents/test_backtest_agent.py`

The Backtesting Agent runs vectorized backtests offline to validate strategy parameters before live trading.

- [ ] **Step 1: Write test**

```python
# tests/agents/test_backtest_agent.py
import pytest
from src.agents.backtest_agent import BacktestAgent

def test_sma_backtest_returns_metrics(sample_ohlcv):
    agent = BacktestAgent()
    result = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.0)
    assert "performance" in result
    assert "outperformance" in result
    assert "total_trades" in result
    assert result["performance"] > 0

def test_mean_reversion_backtest(sample_ohlcv):
    agent = BacktestAgent()
    result = agent.run(sample_ohlcv, strategy="MeanReversion",
                       bb_window=10, bb_dev=1.5, tc=0.0)
    assert "performance" in result
    assert result["total_trades"] >= 0

def test_transaction_costs_reduce_performance(sample_ohlcv):
    agent = BacktestAgent()
    r_no_tc = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.0)
    r_tc = agent.run(sample_ohlcv, strategy="SMA", sma_short=5, sma_long=20, tc=0.001)
    assert r_no_tc["performance"] >= r_tc["performance"]

def test_optimize_sma_returns_valid_params(sample_ohlcv):
    agent = BacktestAgent()
    short, long, perf = agent.optimize_sma(
        sample_ohlcv, short_range=range(3, 8), long_range=range(10, 20), tc=0.0
    )
    assert short < long
    assert perf > 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/agents/test_backtest_agent.py -v
```
Expected: FAILED

- [ ] **Step 3: Implement backtest_agent.py**

```python
# src/agents/backtest_agent.py
from __future__ import annotations
import numpy as np
import pandas as pd
from src.tools.analysis_tools import compute_sma, compute_bollinger_bands

class BacktestAgent:
    """Vectorized backtester for SMA crossover and MeanReversion strategies."""

    def run(
        self,
        df: pd.DataFrame,
        strategy: str = "SMA",
        sma_short: int = 10,
        sma_long: int = 50,
        bb_window: int = 20,
        bb_dev: float = 2.0,
        tc: float = 0.0,
    ) -> dict:
        data = df.copy()
        data["returns"] = np.log(data["close"] / data["close"].shift(1))

        if strategy == "SMA":
            data = compute_sma(data, short=sma_short, long=sma_long)
            data["position"] = np.where(data["sma_short"] > data["sma_long"], 1, -1)
        else:
            data = compute_bollinger_bands(data, window=bb_window, dev=bb_dev)
            data["position"] = np.where(data["close"] < data["lower"], 1, np.nan)
            data["position"] = np.where(data["close"] > data["upper"], -1, data["position"])
            data["position"] = np.where(
                data["distance"] * data["distance"].shift(1) < 0, 0, data["position"]
            )
            data["position"] = data["position"].ffill().fillna(0)

        data.dropna(inplace=True)
        data["strategy"] = data["position"].shift(1) * data["returns"]
        data["trades"] = data["position"].diff().fillna(0).abs()
        data["strategy"] = data["strategy"] - data["trades"] * tc
        data["creturns"] = data["returns"].cumsum().apply(np.exp)
        data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)

        return {
            "performance": float(data["cstrategy"].iloc[-1]),
            "buy_and_hold": float(data["creturns"].iloc[-1]),
            "outperformance": float(data["cstrategy"].iloc[-1] - data["creturns"].iloc[-1]),
            "total_trades": int(data["trades"].sum() / 2),
        }

    def optimize_sma(
        self,
        df: pd.DataFrame,
        short_range: range,
        long_range: range,
        tc: float = 0.0,
    ) -> tuple[int, int, float]:
        best_perf, best_short, best_long = -np.inf, short_range.start, long_range.start
        for s in short_range:
            for l in long_range:
                if s >= l:
                    continue
                result = self.run(df, strategy="SMA", sma_short=s, sma_long=l, tc=tc)
                if result["performance"] > best_perf:
                    best_perf = result["performance"]
                    best_short, best_long = s, l
        return best_short, best_long, best_perf
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/agents/test_backtest_agent.py -v
```
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/agents/backtest_agent.py tests/agents/test_backtest_agent.py
git commit -m "feat: add BacktestAgent with vectorized SMA and MeanReversion backtesting"
```

---

## Task 15: Orchestrator Agent

**Files:**
- Create: `src/agents/orchestrator.py`

- [ ] **Step 1: Implement orchestrator.py**

```python
# src/agents/orchestrator.py
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from src.config import Config
from src.state import TradingSessionState
from src.models.market_data import Bar
from src.tools.ibkr_tools import IBKRClient
from src.agents.market_data_agent import MarketDataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.risk_agent import RiskAgent
from src.agents.execution_agent import ExecutionAgent
from src.agents.monitor_agent import MonitorAgent

logger = logging.getLogger(__name__)

class TradingOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.client = IBKRClient(config.ibkr_host, config.ibkr_port, config.ibkr_client_id)
        self.state = TradingSessionState(symbol=config.symbol)
        self.market_data = MarketDataAgent(client=self.client)
        self.strategy = StrategyAgent(
            model=config.model_strategy, api_key=config.openrouter_api_key
        )
        self.analysis = AnalysisAgent(
            model=config.model_analysis, api_key=config.openrouter_api_key
        )
        self.risk = RiskAgent(
            max_units=config.max_position_units,
            sl_pct=config.stop_loss_pct,
            tp_pct=config.take_profit_pct,
            max_drawdown_pct=config.max_drawdown_pct,
            initial_capital=config.initial_capital,
        )
        self.execution = ExecutionAgent(client=self.client)
        self.monitor = MonitorAgent(
            initial_capital=config.initial_capital,
            max_drawdown_pct=config.max_drawdown_pct,
        )
        self.contract = None
        self.active_strategy = "SMA"

    async def start(self) -> None:
        await self.client.connect()
        logger.info("Connected to IBKR %s:%s", self.config.ibkr_host, self.config.ibkr_port)

        self.contract = self.client.make_forex_contract(
            self.config.symbol, self.config.currency, self.config.exchange
        )
        await self.market_data.load_history(
            self.state, self.contract, self.config.bar_size
        )
        logger.info("Loaded %d historical bars", len(self.state.history.bars))

        self.state.session_active = True
        self.state.session_start = datetime.now(tz=timezone.utc)
        self.state.session_end = self.state.session_start + timedelta(
            hours=self.config.session_duration_hours
        )

        self.active_strategy = self.strategy.select_strategy(self.state)
        logger.info("Selected strategy: %s", self.active_strategy)

        bars = self.client.ib.reqRealTimeBars(
            self.contract, barSize=5, whatToShow="MIDPOINT", useRTH=False
        )
        bars.updateEvent += self._on_bar

        logger.info("Streaming bars. Session ends at %s", self.state.session_end)
        while self.state.session_active:
            self.client.ib.sleep(1)
            result = self.monitor.check(self.state)
            if result.should_stop:
                logger.info("Stopping session: %s", result.reason)
                self.state.session_active = False

        self.client.ib.cancelRealTimeBars(bars)
        await self._shutdown()

    def _on_bar(self, bars, has_new_bar: bool) -> None:
        if not has_new_bar or not self.state.session_active:
            return

        raw = bars[-1]
        bar = Bar(
            timestamp=datetime.now(tz=timezone.utc),
            open=raw.open, high=raw.high, low=raw.low,
            close=raw.close, volume=float(raw.volume),
        )
        self.market_data.on_bar_update(self.state, bar)

        signal = self.analysis.run(self.state, strategy=self.active_strategy)
        logger.info("Signal: %s — %s", signal.direction, signal.reason)

        decision = self.risk.evaluate(self.state, signal)
        self.execution.execute(self.state, decision, self.contract, signal.direction)

    async def _shutdown(self) -> None:
        if self.state.current_position != 0:
            from src.models.signals import Direction
            from src.agents.risk_agent import RiskDecision
            flat = RiskDecision(approved=True, quantity=0, stop_loss=None,
                                take_profit=None, reason="session end — closing all")
            self.execution.execute(self.state, flat, self.contract, Direction.FLAT)

        summary = self.monitor.build_summary(self.state)
        self.monitor.print_summary(summary)
        self.client.disconnect()
```

- [ ] **Step 2: Commit**

```bash
git add src/agents/orchestrator.py
git commit -m "feat: add TradingOrchestrator coordinating all agents in event loop"
```

---

## Task 16: Entry Point and Full Test Run

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Implement main.py**

```python
# src/main.py
import asyncio
import logging
from src.config import load_config
from src.agents.orchestrator import TradingOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def main() -> None:
    config = load_config()
    orchestrator = TradingOrchestrator(config)
    await orchestrator.start()

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify imports resolve**

```bash
python -c "from src.main import main; print('imports OK')"
```
Expected: `imports OK`

- [ ] **Step 3: Run complete test suite**

```bash
pytest tests/ -v
```
Expected: all tests PASSED

- [ ] **Step 4: Commit**

```bash
git add src/main.py
git commit -m "feat: add entry point — run with python src/main.py"
```

---

## Agent Interaction Diagram

```
Bar tick received (ib_async callback)
         │
         ▼
  MarketDataAgent          ← appends Bar to OHLCVHistory, updates current_price
         │
         ▼
  AnalysisAgent            ← computes indicators, calls LLM → Signal (LONG/SHORT/FLAT)
         │
         ▼
  RiskAgent                ← validates drawdown, sizes position → RiskDecision
         │
         ▼
  ExecutionAgent           ← places bracket orders or closes position via ib_async
         │
         ▼
  MonitorAgent             ← checks session end / drawdown / stop events each tick

  StrategyAgent            ← called once at session start to select SMA or MeanReversion
  BacktestAgent            ← called offline before session to validate parameters
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|---|---|
| Full trading cycle | Tasks 8–15 (data → analysis → strategy → risk → execution → monitoring) |
| Claude Agent SDK / OpenRouter | AnalysisAgent, StrategyAgent use OpenRouter base URL (OpenAI-compatible) |
| ib_async / Interactive Brokers | Task 7 IBKRClient, Task 12 ExecutionAgent, Task 15 Orchestrator |
| SMA crossover strategy | analysis_tools.py sma_signal, BacktestAgent |
| Mean Reversion / Bollinger Bands | analysis_tools.py mean_reversion_signal, BacktestAgent |
| Risk management (SL/TP, drawdown) | Tasks 6, 11, 13 |
| Backtesting | Task 14 BacktestAgent |
| uv as package manager | Task 1 uses `uv add` throughout |
| Per-agent LLM assignment | Config model_* fields, OpenRouter model strings |

### Type Consistency

- `Signal.direction` is `Direction` enum throughout — all agents construct with `Direction.X`.
- `RiskDecision.quantity` is `float` — `abs(target - current)` in ExecutionAgent is float-safe.
- `call_llm` function name is consistent between AnalysisAgent and StrategyAgent tests and implementations.
- `OHLCVHistory.bars` is `deque[Bar]` — `len()` works correctly in all tests.
