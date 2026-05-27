"""Strategy factory for creating strategy instances from configuration."""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import yaml

from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.contrarian import ContrarianStrategy
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.strategy_base import Strategy
from src.strategies.tanh_strategy import TanhStrategy

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_STRATEGY_CLASSES = {
    "SMACrossoverStrategy": SMACrossoverStrategy,
    "BollingerBandsStrategy": BollingerBandsStrategy,
    "ContrarianStrategy": ContrarianStrategy,
    "TanhStrategy": TanhStrategy,
}


def _load_params(params_file: str) -> dict:
    """Load strategy parameters from YAML file."""
    if not params_file or not os.path.exists(params_file):
        logger.info("No params file found, using defaults")
        return {}
    with open(params_file) as f:
        return yaml.safe_load(f) or {}


class StrategyFactory:
    """Factory for creating configured strategy instances."""

    @staticmethod
    def create(strategy_name: str, contract, params_file: str = "") -> Strategy:
        """
        Create a strategy instance by name.

        Args:
            strategy_name: Name of the strategy class
            contract: ib_async contract object
            params_file: Optional path to YAML config file for strategy parameters

        Returns:
            Configured Strategy instance

        Raises:
            ValueError: If strategy_name is unknown
        """
        cls = _STRATEGY_CLASSES.get(strategy_name)
        if cls is None:
            raise ValueError(
                f"Unknown strategy: {strategy_name}. "
                f"Available: {list(_STRATEGY_CLASSES.keys())}"
            )

        params = _load_params(params_file)
        logger.info("Creating strategy %s with params: %s", strategy_name, params)
        return cls(name=strategy_name, contract=contract, **params)
