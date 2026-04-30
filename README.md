# trading-agents-01

Independent trading strategies that connect to **Interactive Brokers (IBKR)** for market data and execution. Configurable trading strategies with deterministic, rule-based position calculation.

## Prerequisites

- **Windows + PowerShell** (commands below assume this)
- **Python 3.12+**
- **uv** (recommended) for reproducible installs using `uv.lock`
  - Install: `pip install uv`
- **IBKR Trader Workstation (TWS)** or **IB Gateway** running locally (paper trading recommended)

## Setup

### 1) Create environment and install dependencies

From the repo root:

```bash
# create/update .venv and install locked dependencies
uv sync --dev
```

If you don’t want dev dependencies:

```bash
uv sync
```

### 2) Configure environment variables

Copy the example env file and fill in real values:

```bash
cp .env.example .env
```


IBKR connection defaults (can be changed in `.env`):

- **`IBKR_HOST`**: default `127.0.0.1`
- **`IBKR_PORT`**: default `7497` (commonly TWS paper)
- **`IBKR_CLIENT_ID`**: default `1`

Trading session defaults (can be changed in `.env`):

- **`SYMBOL`**: default `EUR/USD`
- **`EXCHANGE`**: default `IDEALPRO`
- **`CURRENCY`**: default `USD`
- **`BAR_SIZE`**: default `20 mins`
- **`SESSION_DURATION_HOURS`**, **`MAX_POSITION_UNITS`**
- Risk: **`STOP_LOSS_PCT`**, **`TAKE_PROFIT_PCT`**, **`MAX_DRAWDOWN_PCT`**, **`INITIAL_CAPITAL`**

Strategy selection (can be changed in `.env`):

- **`STRATEGY_NAME`**: default `ContrarianStrategy`
- **`STRATEGY_PARAMS_FILE`**: default `` (uses strategy defaults)

## Run

Make sure TWS / IB Gateway is running and API connections are enabled, then start the trading session:
To save the logs with a timestamped filename in the `logs` folder, you can use a single-line command:


### Production

```bash
# macOS/Linux (bash)
uv run python -m src.strategies.main
```

You should see logs like “Connected to IBKR …”, “Loaded historical bars”, and “Streaming bars…”.

### Debugging / Logs


```bash
# macOS/Linux (bash)
uv run python -u -m src.strategies.main 2>&1 | tee "logs/session_$(date +'%Y%m%d_%H%M%S').txt"
```

Ensure the `logs` directory exists before running these commands.



## Run tests

```bash
uv run pytest -q
```

## Troubleshooting

- **IBKR won’t connect**
  - Verify TWS/IB Gateway is running and the API is enabled (and “Read-Only API” is *off* if you want to place trades).
  - Check the port: `7497` is commonly **paper** TWS; `7496` is commonly **live** TWS (varies by setup).
  - Try changing `IBKR_CLIENT_ID` if another client is already connected.

- **Env var errors**
  - Ensure you created `.env` from `.env.example` and configured required settings.

## Project layout

- **`src/strategies/main.py`**: entrypoint for trading sessions
- **`src/strategies/`**: trading strategies (SMA Crossover, Bollinger Bands, Contrarian, Tanh)
- **`src/tools/`**: IBKR client wrappers
- **`src/config.py`**: loads config from `.env` / environment variables
- **`src/state.py`**: trading session state management
- **`tests/`**: unit tests

