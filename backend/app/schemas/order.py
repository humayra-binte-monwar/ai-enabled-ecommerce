from pydantic import BaseModel


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    items: list[OrderItem]
    total: float
    user_id: str | None = None
    user_email: str | None = None


class Order(OrderCreate):
    id: str
    status: str
    created_at: str