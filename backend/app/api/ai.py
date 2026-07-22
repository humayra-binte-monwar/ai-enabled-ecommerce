from fastapi import APIRouter

from app.schemas.ai import ProductFinderRequest, ProductFinderResponse
from app.services.product_finder_service import find_products

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/product-finder", response_model=ProductFinderResponse)
def product_finder(request: ProductFinderRequest):
    return find_products(request.query)