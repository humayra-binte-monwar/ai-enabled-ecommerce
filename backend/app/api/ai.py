from fastapi import APIRouter

from app.schemas.ai import ProductFinderRequest, ProductFinderResponse
from app.services.product_finder_service import find_products
from app.schemas.ai import BundlePlannerRequest, BundlePlannerResponse
from app.services.bundle_planner_service import plan_bundle

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