## File Structure

```
src/strategies/
├── __init__.py           # Exports Strategy, StrategyFactory, all strategy classes
├── [x] strategy_base.py      # Abstract base class Strategy
├── sma_crossover.py      # SMACrossoverStrategy implementation
├── [x] bollinger_bands.py    # BollingerBandsStrategy implementation
├── contrarian.py         # ContrarianStrategy implementation
├── factory.py            # StrategyFactory.create(strategy_name, contract, config)
└── executor.py           # StrategyExecutor - loosely coupled execution driver

config/strategies/
├── sma_crossover.yaml    # Parameters for SMA Crossover
├── bollinger_bands.yaml  # Parameters for Bollinger Bands
└── contrarian.yaml       # Parameters for Contrarian

.env / .env.example
```
