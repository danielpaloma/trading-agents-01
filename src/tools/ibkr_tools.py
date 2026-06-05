# src/tools/ibkr_tools.py
from __future__ import annotations

from datetime import UTC, datetime

from ib_async import (
    CFD,
    IB,
    BarData,
    Contract,
    Forex,
    LimitOrder,
    MarketOrder,
    Stock,
    StopOrder,
    Trade,
)

from src.models.market_data import Bar


class IBKRClient:
    def __init__(self, host: str, port: int, client_id: int):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()

    async def connect(self) -> None:
        await self.ib.connectAsync(self.host, self.port, clientId=self.client_id)

    def disconnect(self) -> None:
        self.ib.disconnect()

    def create_forex_contract(self, pair: str, exchange: str = "IDEALPRO") -> Forex:
        """Create a Forex contract for currency pair trading."""
        return Forex(pair=pair, exchange=exchange)

    def create_cfd_contract(
        self, symbol: str, currency: str = "USD", exchange: str = "IDEALPRO"
    ) -> CFD:
        """Create a CFD contract for index/currency CFDs."""
        return CFD(symbol=symbol, currency=currency, exchange=exchange)

    def create_stock_contract(
        self, symbol: str, currency: str = "USD", exchange: str = "SMART"
    ) -> Stock:
        """Create a Stock contract for equity trading."""
        return Stock(symbol=symbol, currency=currency, exchange=exchange)

    async def qualify(self, contract: Contract) -> Contract:
        """Qualify contract to ensure it's valid for trading."""
        qualified = await self.ib.qualifyContractsAsync(contract)
        if not qualified:
            raise ValueError(f"Contract could not be qualified: {contract}")
        result = qualified[0]
        if isinstance(result, list):
            for r in result:
                if r is not None:
                    return r
            raise ValueError(f"Contract could not be qualified (no valid match): {contract}")
        if result is None:
            raise ValueError(f"Contract could not be qualified (returned None): {contract}")
        return result

    def get_position(self, symbol: str) -> float:
        for pos in self.ib.positions():
            if symbol in pos.contract.localSymbol:
                return pos.position
        return 0.0

    def get_current_price(self, contract: Contract) -> float:
        ticker = self.ib.ticker(contract)
        if ticker and ticker.last:
            return float(ticker.last)
        if ticker and ticker.midpoint():
            return float(ticker.midpoint())
        return 0.0

    async def request_historical_bars(
        self, contract: Contract, bar_size: str = "20 mins", duration: str = "2 D"
    ) -> list[Bar]:
        bars: list[BarData] = await self.ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="MIDPOINT",
            useRTH=False,
        )
        return [
            Bar(
                timestamp=(
                    b.date.replace(tzinfo=UTC)
                    if isinstance(b.date, datetime)
                    else datetime.combine(b.date, datetime.min.time(), tzinfo=UTC)
                ),
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=float(b.volume),
            )
            for b in bars
        ]

    def place_bracket_order(
        self,
        contract: Contract,
        action: str,
        quantity: float,
        stop_loss: float,
        take_profit: float,
    ) -> list[Trade]:
        parent = MarketOrder(action, quantity)
        parent.transmit = False

        sl_action = "SELL" if action == "BUY" else "BUY"
        stop = StopOrder(sl_action, quantity, stop_loss)
        stop.parentId = parent.orderId
        stop.transmit = False

        tp = LimitOrder(sl_action, quantity, take_profit)
        tp.parentId = parent.orderId
        tp.transmit = True

        return [
            self.ib.placeOrder(contract, parent),
            self.ib.placeOrder(contract, stop),
            self.ib.placeOrder(contract, tp),
        ]

    def cancel_all_orders(self, contract: Contract) -> None:
        for trade in self.ib.openTrades():
            if trade.contract.conId == contract.conId:
                self.ib.cancelOrder(trade.order)
