"""Strategy executor - loosely coupled execution driver."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from src.strategies.strategy_base import Strategy

if TYPE_CHECKING:
    from src.state import TradingSessionState

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Loosely coupled executor that drives a strategy against the trading session state.

    Does NOT place orders directly — returns the target position for the execution
    agent to act upon.
    """

    def __init__(self, strategy: Strategy):
        """
        Initialize executor with a strategy instance.

        Args:
            strategy: Any Strategy subclass instance
        """
        self.strategy = strategy

    def compute_target(self, state: TradingSessionState) -> int:
        """
        Compute target position from current market data.

        Args:
            state: Current TradingSessionState with history

        Returns:
            Target position in units
        """
        bars = list(state.history.bars)
        if not bars:
            logger.debug("No bars available, returning 0 position")
            return 0

        target = self.strategy.calculate_position(bars)
        logger.debug(
            "Strategy %s computed target position: %d",
            self.strategy.name,
            target,
        )
        return target
