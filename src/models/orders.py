# src/models/orders.py
from datetime import datetime

from pydantic import BaseModel


class OrderRequest(BaseModel):
    symbol: str
    action: str
    quantity: float
    order_type: str = "MKT"
    stop_loss: float | None = None
    take_profit: float | None = None


class OrderFill(BaseModel):
    order_id: int
    symbol: str
    action: str
    quantity: float
    fill_price: float
    timestamp: datetime
