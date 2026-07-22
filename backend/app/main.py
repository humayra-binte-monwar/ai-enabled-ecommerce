from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.ai import router as ai_router

app = FastAPI(
    title="AI Grocery Commerce API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(orders_router)
app.include_router(ai_router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}