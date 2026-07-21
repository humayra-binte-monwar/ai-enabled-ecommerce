import json
from pathlib import Path

from app.core.supabase_client import get_supabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "processed" / "products.json"


def seed_products():
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        products = json.load(file)

    supabase = get_supabase()

    for product in products:
        supabase.table("products").upsert(product).execute()

    print(f"Seeded {len(products)} products.")


if __name__ == "__main__":
    seed_products()