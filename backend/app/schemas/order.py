from uuid import UUID

from pydantic import BaseModel, Field


class CheckoutItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, le=99)


class CheckoutCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    items: list[CheckoutItem] = Field(min_length=1)
    idempotency_key: UUID


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    unit_price: float
    quantity: int


class Order(BaseModel):
    id: str
    customer_name: str
    customer_phone: str
    customer_address: str
    subtotal: float
    delivery_fee: float
    total: float
    currency: str
    status: str
    created_at: str
    items: list[OrderItem] = Field(default_factory=list)


class CheckoutSession(BaseModel):
    order_id: str
    payment_url: str
