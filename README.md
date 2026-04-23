# trading-agents-01

Multi-agent trading loop that connects to **Interactive Brokers (IBKR)** for market data + execution, and uses **LLMs (via OpenRouter / Anthropic)** for analysis/strategy decisions.

## Prerequisites

- **Windows + PowerShell** (commands below assume this)
- **Python 3.12+**
- **uv** (recommended) for reproducible installs using `uv.lock`
  - Install: `pip install uv`
- **IBKR Trader Workstation (TWS)** or **IB Gateway** running locally (paper trading recommended)

## Setup

### 1) Create environment and install dependencies

From the repo root:

```powershell
# create/update .venv and install locked dependencies
uv sync --dev
```

If you don’t want dev dependencies:

```powershell
uv sync
```

### 2) Configure environment variables

Copy the example env file and fill in real values:

```powershell
Copy-Item .env.example .env
```

Required keys:

- **`ANTHROPIC_API_KEY`**: used by Anthropic directly (some agent stacks may rely on it)
- **`OPENROUTER_API_KEY`**: used by agents that call OpenRouter (strategy/analysis in this codebase)

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

## Run

Make sure TWS / IB Gateway is running and API connections are enabled, then start the orchestrator:

```powershell
uv run python .\src\main.py
```

You should see logs like “Connected to IBKR …”, “Loaded historical bars”, and “Streaming bars…”.

## Run tests

```powershell
uv run pytest -q
```

## Troubleshooting

- **IBKR won’t connect**
  - Verify TWS/IB Gateway is running and the API is enabled (and “Read-Only API” is *off* if you want to place trades).
  - Check the port: `7497` is commonly **paper** TWS; `7496` is commonly **live** TWS (varies by setup).
  - Try changing `IBKR_CLIENT_ID` if another client is already connected.

- **Env var errors like `KeyError: 'OPENROUTER_API_KEY'`**
  - Ensure you created `.env` and filled in the required keys.

## Project layout

- **`src/main.py`**: entrypoint
- **`src/agents/`**: orchestrator + specialized agents
- **`src/tools/`**: IBKR client wrappers and utilities
- **`src/config.py`**: loads config from `.env` / environment variables
- **`tests/`**: unit tests

