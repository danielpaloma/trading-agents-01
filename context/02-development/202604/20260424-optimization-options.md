
## Initial analysis

main
    (config, orchestrator)
    Orchestrator
        Monitor (loop)
            1. Market data
            2. Strategy
            3. Analysis
            4. Risk - evaluate
            5. Execution
            (Backtesting) --> Mode 2





## 1. Market data agent

This can be simplified to a couple of functions.
No need to create an agent. Simpler mental model

### current implementation
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

## 2. Strategy Agent

Computes simple returns --> should be log returns instead?
Strategy definition not found, it is sending a message to LLM asking for best strategy

msg = (
            f"Annualized volatility: {volatility:.4f}\n"
            f"Returns autocorrelation (lag-1): {autocorr:.4f}\n"
            f"Trend strength (|mean|/std, 20-bar): {trend_strength:.4f}\n"
            f"Number of bars: {len(df)}\n"
            f"Select the best strategy."
        )

## 3. Analysis Agent

It computes strategy parameters and ask LLM to select strategy.

user_msg = (
                f"Strategy: Mean Reversion (Bollinger Bands)\n"
                f"Current price: {state.current_price:.5f}\n"
                f"SMA({bb_window}): {last['sma']:.5f}\n"
                f"Upper band: {last['upper']:.5f}\n"
                f"Lower band: {last['lower']:.5f}\n"
                f"Distance from SMA: {last['distance']:.5f}\n"
                f"Suggest a trading signal."
            )

## 4. Risk - evaluate

## 5. Execution

[x] There is no clarity on how order placement obey the strategy?


## Strategies

* Include a strategy registry, capturing context, rules, parameters, definitions for each strategy


## Backtesting

* Include a separate module for backtesting