# tests/tools/test_ibkr_tools.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.tools.ibkr_tools import IBKRClient


@pytest.fixture
def mock_ib():
    ib = MagicMock()
    ib.connectAsync = AsyncMock()
    ib.disconnect = MagicMock()
    ib.positions = MagicMock(return_value=[])
    ib.placeOrder = MagicMock(return_value=MagicMock(orderId=42))
    return ib

async def test_get_position_empty(mock_ib):
    client = IBKRClient(host="127.0.0.1", port=7497, client_id=1)
    client.ib = mock_ib
    pos = client.get_position("EUR")
    assert pos == 0.0