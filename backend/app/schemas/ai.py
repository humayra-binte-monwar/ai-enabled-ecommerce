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
    recommended_quantity: int
    suggested_quantity: int
    reason: str


class BundlePlannerResponse(BaseModel):
    summary: str
    estimated_total: float
    remaining_budget: float
    items: list[BundlePlannerItem]


class CartOptimizerItem(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    quantity: int


class CartOptimizerRequest(BaseModel):
    items: list[CartOptimizerItem]
    goal: str | None = None


class CartOptimizerSuggestion(BaseModel):
    type: str
    message: str
    product_id: str | None = None
    product_name: str | None = None
    category: str | None = None
    price: float | None = None
    unit: str | None = None
    image_url: str | None = None
    product_url: str | None = None


class CartOptimizerResponse(BaseModel):
    summary: str
    cart_total: float
    suggestions: list[CartOptimizerSuggestion]
