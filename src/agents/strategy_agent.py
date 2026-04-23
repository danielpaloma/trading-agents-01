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