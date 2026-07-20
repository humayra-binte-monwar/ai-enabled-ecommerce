from fastapi import APIRouter, HTTPException, Query

from app.schemas.product import Product
from app.services.product_service import get_product_by_id, load_products

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[Product])
def list_products(
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
):
    products = load_products()

    if search:
        search_lower = search.lower()
        products = [
            product
            for product in products
            if search_lower in product.name.lower()
            or search_lower in product.category.lower()
            or (product.brand and search_lower in product.brand.lower())
        ]

    if category:
        products = [
            product
            for product in products
            if product.category.lower() == category.lower()
        ]

    return products


@router.get("/{product_id}", response_model=Product)
def product_detail(product_id: str):
    product = get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product