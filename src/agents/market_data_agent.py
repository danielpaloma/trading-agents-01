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