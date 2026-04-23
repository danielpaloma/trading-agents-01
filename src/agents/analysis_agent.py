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