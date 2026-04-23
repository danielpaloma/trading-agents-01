# src/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    anthropic_api_key: str
    openrouter_api_key: str
    model_orchestrator: str
    model_market_data: str
    model_analysis: str
    model_strategy: str
    model_risk: str
    model_execution: str
    model_monitor: str
    ibkr_host: str
    ibkr_port: int
    ibkr_client_id: int
    symbol: str
    exchange: str
    currency: str
    bar_size: str
    session_duration_hours: float
    max_position_units: float
    stop_loss_pct: float
    take_profit_pct: float
    max_drawdown_pct: float
    initial_capital: float

def load_config() -> Config:
    return Config(
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
        model_orchestrator=os.getenv("MODEL_ORCHESTRATOR", "anthropic/claude-sonnet-4-6"),
        model_market_data=os.getenv("MODEL_MARKET_DATA", "anthropic/claude-haiku-4-5"),
        model_analysis=os.getenv("MODEL_ANALYSIS", "anthropic/claude-sonnet-4-6"),
        model_strategy=os.getenv("MODEL_STRATEGY", "anthropic/claude-sonnet-4-6"),
        model_risk=os.getenv("MODEL_RISK", "anthropic/claude-sonnet-4-6"),
        model_execution=os.getenv("MODEL_EXECUTION", "anthropic/claude-haiku-4-5"),
        model_monitor=os.getenv("MODEL_MONITOR", "anthropic/claude-haiku-4-5"),
        ibkr_host=os.getenv("IBKR_HOST", "127.0.0.1"),
        ibkr_port=int(os.getenv("IBKR_PORT", "7497")),
        ibkr_client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        symbol=os.getenv("SYMBOL", "EUR/USD"),
        exchange=os.getenv("EXCHANGE", "IDEALPRO"),
        currency=os.getenv("CURRENCY", "USD"),
        bar_size=os.getenv("BAR_SIZE", "20 mins"),
        session_duration_hours=float(os.getenv("SESSION_DURATION_HOURS", "8")),
        max_position_units=float(os.getenv("MAX_POSITION_UNITS", "100000")),
        stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.005")),
        take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.010")),
        max_drawdown_pct=float(os.getenv("MAX_DRAWDOWN_PCT", "0.02")),
        initial_capital=float(os.getenv("INITIAL_CAPITAL", "10000")),
    )
