from pydantic import BaseModel, Field
from typing import Any, Literal

order_status = Literal["PENDING", "PAID", "CANCELED", "SHIPPED"]


class OrderItem(BaseModel):
    name_product: str
    count_product: int
    price_product: float


class OrderCreateIn(BaseModel):
    items: list[OrderItem]
    total_price: float


class OrderPatchIn(BaseModel):
    status: order_status


class OrderOut(BaseModel):
    id: int
    user_id: int
    items: list[OrderItem]
    total_price: float
    status: order_status
    created_at: str
