from app.core.supabase_client import get_supabase
from app.schemas.product import Product


def load_products() -> list[Product]:
    supabase = get_supabase()

    response = supabase.table("products").select("*").order("name").execute()

    return [Product(**item) for item in response.data]


def get_product_by_id(product_id: str) -> Product | None:
    supabase = get_supabase()

    response = (
        supabase.table("products")
        .select("*")
        .eq("id", product_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return Product(**response.data[0])
