import json
from pathlib import Path

from app.core.supabase_client import get_supabase
from app.schemas.product import Product
from app.services.embedding_service import EMBEDDING_MODEL, content_hash, embed_texts, product_document, to_pgvector
from app.services.product_tagging_service import enrich_product

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "processed" / "products.json"
BATCH_SIZE = 32


def load_seed_products() -> list[Product]:
    with PRODUCTS_FILE.open("r", encoding="utf-8-sig") as file:
        records = json.load(file)
    return [enrich_product(Product(**record)) for record in records]


def generate_product_embeddings():
    products = load_seed_products()
    supabase = get_supabase()
    written = 0

    for start in range(0, len(products), BATCH_SIZE):
        batch = products[start : start + BATCH_SIZE]
        vectors = embed_texts([product_document(product) for product in batch])
        rows = [
            {
                "product_id": product.id,
                "content_hash": content_hash(product),
                "model": EMBEDDING_MODEL,
                "embedding_384": to_pgvector(vector),
            }
            for product, vector in zip(batch, vectors, strict=True)
        ]
        supabase.table("product_embeddings").upsert(
            rows, on_conflict="product_id"
        ).execute()
        written += len(rows)
        print(f"Embedded {written}/{len(products)} products")

    print(f"Stored {written} {EMBEDDING_MODEL} embeddings in Supabase.")


if __name__ == "__main__":
    generate_product_embeddings()
