from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.ai import router as ai_router
from app.api.payments import router as payments_router
from app.api.search import router as search_router
from app.core.settings import get_settings

settings = get_settings()
allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
] or [settings.frontend_url, "http://localhost:3000"]

app = FastAPI(
    title="AI Grocery Commerce API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(orders_router)
app.include_router(ai_router)
app.include_router(payments_router)
app.include_router(search_router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
