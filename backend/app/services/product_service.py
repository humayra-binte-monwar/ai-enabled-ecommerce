import json
from pathlib import Path

from app.schemas.product import Product

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "processed" / "products.json"


def load_products() -> list[Product]:
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [Product(**item) for item in data]


def get_product_by_id(product_id: str) -> Product | None:
    for product in load_products():
        if product.id == product_id:
            return product

    return None