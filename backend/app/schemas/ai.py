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


class BundlePlannerRequest(BaseModel):
    budget: float
    people: int
    duration_days: int
    meal_type: str
    preference: str | None = None


class BundlePlannerItem(BaseModel):
    id: str
    name: str
    category: str
    price: float
    unit: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    suggested_quantity: int
    reason: str


class BundlePlannerResponse(BaseModel):
    summary: str
    estimated_total: float
    remaining_budget: float
    items: list[BundlePlannerItem]
