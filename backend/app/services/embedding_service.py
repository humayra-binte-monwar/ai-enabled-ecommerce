from functools import lru_cache
from hashlib import sha256

from app.schemas.product import Product

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384


def product_document(product: Product) -> str:
    """Create the retrieval document used for a product embedding."""
    fields = [
        product.name,
        product.brand,
        product.normalized_category or product.category,
        product.category,
        product.product_type,
        product.unit,
        " ".join(product.tags),
    ]
    return ". ".join(field.strip() for field in fields if field and field.strip())


def content_hash(product: Product) -> str:
    return sha256(product_document(product).encode("utf-8")).hexdigest()


@lru_cache
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL, device="cpu")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embeddings = get_embedding_model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return [embedding.astype(float).tolist() for embedding in embeddings]


def to_pgvector(vector: list[float]) -> str:
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(vector)}."
        )
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
