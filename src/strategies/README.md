# Trading Strategies Module

Defines trading strategies with configurable parameters and loose coupling to execution.

**Architecture:** The strategies module exposes a base class `Strategy` that all strategies inherit. A factory function reads strategy name and parameters from environment/config and returns the appropriate strategy instance. Each strategy implements `calculate_position(bars) -> int` returning target position. Execution agent uses the strategy without coupling to concrete implementations.

**Tech Stack:** Python 3.12+, pandas, numpy, PyYAML, standard logging (to `./logs`)

---

## File Structure

```
src/strategies/
├── __init__.py           # Exports Strategy, StrategyFactory, all strategy classes
├── strategy_base.py      # Abstract base class Strategy
├── sma_crossover.py      # SMACrossoverStrategy implementation
├── bollinger_bands.py    # BollingerBandsStrategy implementation
├── contrarian.py         # ContrarianStrategy implementation
├── factory.py            # StrategyFactory.create(strategy_name, contract, config)
└── executor.py           # StrategyExecutor - loosely coupled execution driver

config/strategies/
├── sma_crossover.yaml    # Parameters for SMA Crossover
├── bollinger_bands.yaml  # Parameters for Bollinger Bands
└── contrarian.yaml       # Parameters for Contrarian

.env / .env.example
```

---

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


