# Trading Strategies Module

Defines trading strategies with configurable parameters and loose coupling to execution.

## Available Strategies

| Strategy | Description |
|----------|-------------|
| `SMACrossoverStrategy` | Long when short SMA > long SMA, short otherwise |
| `BollingerBandsStrategy` | Long when price < lower band, short when > upper band |
| `ContrarianStrategy` | Trades against recent price momentum |

## Configuration

Strategies are configured via YAML files in `config/strategies/`.

### Example: `config/strategies/contrarian.yaml`

```yaml
window: 1
units: 1000
```

### Selecting a Strategy

Set in `.env`:

```bash
STRATEGY_NAME=ContrarianStrategy
STRATEGY_PARAMS_FILE=config/strategies/contrarian.yaml
```

If `STRATEGY_PARAMS_FILE` is empty, default parameters are used.

## Usage

```python
from src.agents.ibkr_tools import IBKRClient
from src.strategies import StrategyFactory, StrategyExecutor
from src.config import load_config

config = load_config()
client = IBKRClient(config.ibkr)
contract = client.get_contract(config.instrument)

strategy = StrategyFactory.create(
    config.strategy.name,
    contract,
    config.strategy.params_file,
)
executor = StrategyExecutor(strategy)
target = executor.compute_target(state)
```

## Logs

All strategy activity is logged to `./logs/`.
