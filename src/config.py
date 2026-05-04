# src/config.py
"""Configuration management for Trading Agents."""
import os
import re
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_float(key: str, default: str) -> float:
    """Get float from env, stripping inline comments."""
    value = os.getenv(key, default)
    value = re.sub(r'#.*$', '', value).strip()
    return float(value)


@dataclass
class ModelConfig:
    """LLM model configuration."""
    anthropic_api_key: str
    openrouter_api_key: str
    model_orchestrator: str
    model_market_data: str
    model_analysis: str
    model_strategy: str
    model_risk: str
    model_execution: str
    model_monitor: str


@dataclass
class IBKRConfig:
    """Interactive Brokers connection configuration."""
    host: str
    port: int
    client_id: int


@dataclass
class InstrumentConfig:
    """Trading instrument configuration."""
    instrument_type: str  # STOCK, FOREX, CFD
    symbol: str
    exchange: str
    currency: str


@dataclass
class SessionConfig:
    """Trading session configuration."""
    bar_size: str
    session_duration_hours: float
    max_position_units: float


@dataclass
class RiskConfig:
    """Risk and money management configuration."""
    stop_loss_pct: float
    take_profit_pct: float
    max_drawdown_pct: float
    initial_capital: float


@dataclass
class StrategyConfig:
    """Trading strategy configuration."""
    name: str
    params_file: str  # path to YAML config file for this strategy


@dataclass
class Config:
    """Main configuration container."""
    model: ModelConfig
    ibkr: IBKRConfig
    instrument: InstrumentConfig
    session: SessionConfig
    risk: RiskConfig
    strategy: StrategyConfig  # NEW


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config(
        model=ModelConfig(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            model_orchestrator=os.getenv("MODEL_ORCHESTRATOR", "openai/gpt-oss-120b:free"),
            model_market_data=os.getenv("MODEL_MARKET_DATA", "openai/gpt-oss-120b:free"),
            model_analysis=os.getenv("MODEL_ANALYSIS", "openai/gpt-oss-120b:free"),
            model_strategy=os.getenv("MODEL_STRATEGY", "openai/gpt-oss-120b:free"),
            model_risk=os.getenv("MODEL_RISK", "openai/gpt-oss-120b:free"),
            model_execution=os.getenv("MODEL_EXECUTION", "openai/gpt-oss-120b:free"),
            model_monitor=os.getenv("MODEL_MONITOR", "openai/gpt-oss-120b:free"),
        ),
        ibkr=IBKRConfig(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=int(os.getenv("IBKR_PORT", "7497")),
            client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        ),
        instrument=InstrumentConfig(
            instrument_type=os.getenv("INSTRUMENT_TYPE", "FOREX"),
            symbol=os.getenv("SYMBOL", "EURUSD"),
            exchange=os.getenv("EXCHANGE", "IDEALPRO"),
            currency=os.getenv("CURRENCY", "USD"),
        ),
        session=SessionConfig(
            bar_size=os.getenv("BAR_SIZE", "1 min"),
            session_duration_hours=_get_float("SESSION_DURATION_HOURS", "0.01666"),
            max_position_units=_get_float("MAX_POSITION_UNITS", "10"),
        ),
        risk=RiskConfig(
            stop_loss_pct=_get_float("STOP_LOSS_PCT", "0.005"),
            take_profit_pct=_get_float("TAKE_PROFIT_PCT", "0.010"),
            max_drawdown_pct=_get_float("MAX_DRAWDOWN_PCT", "0.02"),
            initial_capital=_get_float("INITIAL_CAPITAL", "1000"),
        ),
        strategy=StrategyConfig(
            name=os.getenv("STRATEGY_NAME", "ContrarianStrategy"),
            params_file=os.getenv("STRATEGY_PARAMS_FILE", ""),
        ),
    )