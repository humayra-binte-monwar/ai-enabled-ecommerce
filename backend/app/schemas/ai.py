from pydantic import BaseModel


class ProductFinderRequest(BaseModel):
    query: str


class ProductFinderProduct(BaseModel):
    id: str
    name: str
    category: str
    price: float
    unit: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    reason: str


class ProductFinderResponse(BaseModel):
    summary: str
    products: list[ProductFinderProduct]