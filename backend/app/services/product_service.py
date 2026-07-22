import json
from pathlib import Path

from app.core.supabase_client import get_supabase
from app.schemas.product import Product
from app.services.product_tagging_service import enrich_product

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "processed" / "products.json"


def load_local_products() -> list[Product]:
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        products = json.load(file)

    return [enrich_product(Product(**item)) for item in products]


def load_products() -> list[Product]:
    supabase = get_supabase()

    try:
        response = supabase.table("products").select("*").order("name").execute()
    except Exception:
        return load_local_products()

    return [enrich_product(Product(**item)) for item in response.data]


def get_product_by_id(product_id: str) -> Product | None:
    supabase = get_supabase()

    try:
        response = (
            supabase.table("products")
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
    except Exception:
        return next(
            (product for product in load_local_products() if product.id == product_id),
            None,
        )

    if not response.data:
        return None

    return enrich_product(Product(**response.data[0]))
