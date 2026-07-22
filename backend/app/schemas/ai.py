from pydantic import BaseModel, Field


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
    tags: list[str] = Field(default_factory=list)
    normalized_category: str | None = None
    product_type: str | None = None
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


class ChatCartItem(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    quantity: int


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str | None = None
    cart_items: list[ChatCartItem] = Field(default_factory=list)
    confirm_actions: bool = False


class ChatProductCard(BaseModel):
    id: str
    name: str
    category: str
    price: float
    unit: str | None = None
    image_url: str | None = None
    product_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    normalized_category: str | None = None
    product_type: str | None = None
    reason: str | None = None


class ChatCartAction(BaseModel):
    type: str
    product_id: str | None = None
    product_name: str | None = None
    quantity: int | None = None
    requires_confirmation: bool = True
    message: str
    product: ChatProductCard | None = None


class ChatCitation(BaseModel):
    product_id: str
    source_url: str | None = None


class ChatResponse(BaseModel):
    message: str
    intent: str
    products: list[ChatProductCard] = Field(default_factory=list)
    cart_actions: list[ChatCartAction] = Field(default_factory=list)
    citations: list[ChatCitation] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    fallback: bool = False
