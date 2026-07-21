from fastapi import APIRouter

from app.schemas.order import Order, OrderCreate
from app.services.order_service import create_order, load_orders

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[Order])
def list_orders():
    return load_orders()


@router.post("", response_model=Order, status_code=201)
def submit_order(order_data: OrderCreate):
    return create_order(order_data)