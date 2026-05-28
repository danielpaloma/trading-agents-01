# tests/conftest.py

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2024-01-01", periods=50, freq="20min", tz="UTC")
    np.random.seed(42)
    close = 1.1000 + np.cumsum(np.random.randn(50) * 0.0005)
    return pd.DataFrame(
        {
            "open": close - 0.0002,
            "high": close + 0.0003,
            "low": close - 0.0003,
            "close": close,
            "volume": np.random.randint(100, 1000, 50).astype(float),
        },
        index=dates,
    )
