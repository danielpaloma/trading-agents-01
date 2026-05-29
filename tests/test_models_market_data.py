# tests/test_models_market_data.py
from datetime import UTC, datetime

from src.models.market_data import Bar, OHLCVHistory


def test_bar_creation():
    bar = Bar(
        timestamp=datetime(2024, 1, 1, 9, 0, tzinfo=UTC),
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=1.1005,
        volume=500,
    )
    assert bar.close == 1.1005


def test_ohlcv_history_append_and_dataframe(sample_ohlcv):
    history = OHLCVHistory(max_bars=100)
    for ts, row in sample_ohlcv.iterrows():
        history.append(
            Bar(
                timestamp=ts,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
            )
        )
    df = history.to_dataframe()
    assert len(df) == 50
    assert "close" in df.columns


def test_ohlcv_history_max_bars():
    history = OHLCVHistory(max_bars=5)
    for i in range(10):
        history.append(
            Bar(
                timestamp=datetime(2024, 1, 1, i, 0, tzinfo=UTC),
                open=1.1,
                high=1.11,
                low=1.09,
                close=1.10,
                volume=100,
            )
        )
    assert len(history.bars) == 5
