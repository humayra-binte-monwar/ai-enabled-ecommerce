from fastapi import APIRouter

from app.services.bundle_planner_service import plan_bundle
from app.services.cart_optimizer_service import optimize_cart
from app.services.product_finder_service import find_products
from app.ai.agent import run_chat
from app.schemas.ai import (
    BundlePlannerRequest,
    BundlePlannerResponse,
    CartOptimizerRequest,
    CartOptimizerResponse,
    ChatRequest,
    ChatResponse,
    ProductFinderRequest,
    ProductFinderResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/product-finder", response_model=ProductFinderResponse)
def product_finder(request: ProductFinderRequest):
    return find_products(request.query)


@router.post("/bundle-planner", response_model=BundlePlannerResponse)
def bundle_planner(request: BundlePlannerRequest):
    return plan_bundle(
        budget=request.budget,
        people=request.people,
        duration_days=request.duration_days,
        meal_type=request.meal_type,
        preference=request.preference,
    )


@router.post("/cart-optimizer", response_model=CartOptimizerResponse)
def cart_optimizer(request: CartOptimizerRequest):
    return optimize_cart(items=request.items, goal=request.goal)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return run_chat(request)
