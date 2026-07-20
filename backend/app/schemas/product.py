from pydantic import BaseModel


class Product(BaseModel):
    id: str
    name: str
    category: str
    brand: str | None = None
    price: float
    unit: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    stock_status: str = "in_stock"