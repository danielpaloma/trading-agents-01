# src/strategies/strategy_base.py
from __future__ import annotations
from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.market_data import Bar

logger = logging.getLogger(__name__)


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.

    Concrete strategies must implement `calculate_position(bars) -> int`.
    """

    def __init__(self, name: str, contract, units: int = 1000):
        """
        Initialize strategy.

        Args:
            name: Strategy identifier (e.g., "SMA", "BollingerBands")
            contract: ib_async contract object
            units: Position size in units (default 1000)
        """
        self.name = name
        self.contract = contract
        self.units = units

    @abstractmethod
    def calculate_position(self, bars: list[Bar]) -> int:
        """
        Calculate target position from market bars.

        Args:
            bars: List of OHLCV Bar objects, oldest first

        Returns:
            Target position in units (positive = long, negative = short, 0 = neutral)
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(units={self.units})"