# Trading Strategies Module

Defines trading strategies with configurable parameters and loose coupling to execution.

## Available Strategies

| Strategy | Description |
|----------|-------------|
| `SMACrossoverStrategy` | Long when short SMA > long SMA, short otherwise |
| `BollingerBandsStrategy` | Long when price < lower band, short when > upper band |
| `ContrarianStrategy` | Trades against recent price momentum |

## Procedure

1. Configure variables using .env file
2. Configure strategy parameters via YAML files in `config/strategies/`.
3. Log in to TWS (Interactive Brokers) prior to run trading session.
4. Run Trading Session with the selected strategy!

## Configuration

Strategies are configured via YAML files in `config/strategies/`.

### Example: `config/strategies/contrarian.yaml`

```yaml
window: 1
units: 10
```

### Selecting a Strategy

Set in `.env`:

```bash
STRATEGY_NAME=ContrarianStrategy
STRATEGY_PARAMS_FILE=config/strategies/contrarian.yaml
```

If `STRATEGY_PARAMS_FILE` is empty, default parameters are used.

## Usage

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


