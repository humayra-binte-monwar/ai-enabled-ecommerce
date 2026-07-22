import re

from fastapi import HTTPException, status

from app.core.supabase_client import get_supabase
from app.schemas.ai import HybridSearchRequest
from app.services.embedding_service import embed_texts, to_pgvector


def infer_max_price(query: str) -> float | None:
    match = re.search(
        r"(?:under|below|within|max(?:imum)?|less than)\s*(?:tk|taka)?\s*(\d+(?:\.\d+)?)",
        query.lower(),
    )
    return float(match.group(1)) if match else None


def hybrid_search(request: HybridSearchRequest) -> dict:
    max_price = request.max_price if request.max_price is not None else infer_max_price(request.query)
    vector = to_pgvector(embed_texts([request.query])[0])

    try:
        response = get_supabase().rpc(
            "match_products_hybrid",
            {
                "query_embedding": vector,
                "match_count": request.limit,
                "filter_category": request.category,
                "min_price": request.min_price,
                "max_price": max_price,
            },
        ).execute()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is not ready. Generate the product embedding index first.",
        ) from error

    return {
        "query": request.query,
        "applied_filters": {
            "category": request.category,
            "min_price": request.min_price,
            "max_price": max_price,
        },
        "products": response.data,
    }
