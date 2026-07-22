from fastapi import APIRouter

from app.schemas.ai import HybridSearchRequest, HybridSearchResponse
from app.services.hybrid_search_service import hybrid_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/hybrid", response_model=HybridSearchResponse)
def search_catalog(request: HybridSearchRequest):
    return hybrid_search(request)
