from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field, model_validator

order_status = Literal["PENDING", "PAID", "CANCELED", "SHIPPED"]


class OrderItem(BaseModel):
    name_product: str
    count_product: int = Field(gt=0)
    price_product: float = Field(gt=0)


class OrderCreateIn(BaseModel):
    items: list[OrderItem] = Field(min_length=1)
    total_price: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_total_price(self):
        calculated_total = sum(item.count_product * item.price_product for item in self.items)
        if abs(calculated_total - self.total_price) > 1e-6:
            raise ValueError("Итоговая цена не соответствует сумме товаров")
        return self


class OrderPatchIn(BaseModel):
    status: order_status


class OrderOut(BaseModel):
    id: UUID
    user_id: int
    items: list[OrderItem]
    total_price: float
    status: order_status
    created_at: str
