import json
from pathlib import Path

from app.core.supabase_client import get_supabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "processed" / "products.json"


def seed_products():
    with PRODUCTS_FILE.open("r", encoding="utf-8-sig") as file:
        products = json.load(file)

    supabase = get_supabase()

    batch_size = 100
    for start in range(0, len(products), batch_size):
        batch = products[start : start + batch_size]
        supabase.table("products").upsert(batch).execute()

    print(f"Seeded {len(products)} products in batches of {batch_size}.")


if __name__ == "__main__":
    seed_products()
