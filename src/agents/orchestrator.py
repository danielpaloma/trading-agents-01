# src/agents/orchestrator.py
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from src.config import Config
from src.state import TradingSessionState
from src.models.market_data import Bar
from src.tools.ibkr_tools import IBKRClient
from src.agents.market_data_agent import MarketDataAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.risk_agent import RiskAgent
from src.agents.execution_agent import ExecutionAgent
from src.agents.monitor_agent import MonitorAgent

logger = logging.getLogger(__name__)

class TradingOrchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.client = IBKRClient(config.ibkr_host, config.ibkr_port, config.ibkr_client_id)
        self.state = TradingSessionState(symbol=config.symbol)
        self.market_data = MarketDataAgent(client=self.client)
        self.strategy = StrategyAgent(
            model=config.model_strategy, api_key=config.openrouter_api_key
        )
        self.analysis = AnalysisAgent(
            model=config.model_analysis, api_key=config.openrouter_api_key
        )
        self.risk = RiskAgent(
            max_units=config.max_position_units,
            sl_pct=config.stop_loss_pct,
            tp_pct=config.take_profit_pct,
            max_drawdown_pct=config.max_drawdown_pct,
            initial_capital=config.initial_capital,
        )
        self.execution = ExecutionAgent(client=self.client)
        self.monitor = MonitorAgent(
            initial_capital=config.initial_capital,
            max_drawdown_pct=config.max_drawdown_pct,
        )
        self.contract = None
        self.active_strategy = "SMA"

    async def start(self) -> None:
        await self.client.connect()
        logger.info("Connected to IBKR %s:%s", self.config.ibkr_host, self.config.ibkr_port)

        self.contract = self.client.make_forex_contract(
            self.config.symbol, self.config.currency, self.config.exchange
        )
        await self.market_data.load_history(
            self.state, self.contract, self.config.bar_size
        )
        logger.info("Loaded %d historical bars", len(self.state.history.bars))

        self.state.session_active = True
        self.state.session_start = datetime.now(tz=timezone.utc)
        self.state.session_end = self.state.session_start + timedelta(
            hours=self.config.session_duration_hours
        )

        self.active_strategy = self.strategy.select_strategy(self.state)
        logger.info("Selected strategy: %s", self.active_strategy)

        bars = self.client.ib.reqRealTimeBars(
            self.contract, barSize=5, whatToShow="MIDPOINT", useRTH=False
        )
        bars.updateEvent += self._on_bar

        logger.info("Streaming bars. Session ends at %s", self.state.session_end)
        while self.state.session_active:
            self.client.ib.sleep(1)
            result = self.monitor.check(self.state)
            if result.should_stop:
                logger.info("Stopping session: %s", result.reason)
                self.state.session_active = False

        self.client.ib.cancelRealTimeBars(bars)
        await self._shutdown()

    def _on_bar(self, bars, has_new_bar: bool) -> None:
        if not has_new_bar or not self.state.session_active:
            return

        raw = bars[-1]
        bar = Bar(
            timestamp=datetime.now(tz=timezone.utc),
            open=raw.open, high=raw.high, low=raw.low,
            close=raw.close, volume=float(raw.volume),
        )
        self.market_data.on_bar_update(self.state, bar)

        signal = self.analysis.run(self.state, strategy=self.active_strategy)
        logger.info("Signal: %s — %s", signal.direction, signal.reason)

        decision = self.risk.evaluate(self.state, signal)
        self.execution.execute(self.state, decision, self.contract, signal.direction)

    async def _shutdown(self) -> None:
        if self.state.current_position != 0:
            from src.models.signals import Direction
            from src.agents.risk_agent import RiskDecision
            flat = RiskDecision(approved=True, quantity=0, stop_loss=None,
                                take_profit=None, reason="session end — closing all")
            self.execution.execute(self.state, flat, self.contract, Direction.FLAT)

        summary = self.monitor.build_summary(self.state)
        self.monitor.print_summary(summary)
        self.client.disconnect()
