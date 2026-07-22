from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser, require_current_user
from app.schemas.order import CheckoutCreate, CheckoutSession, Order
from app.services.order_service import create_pending_order, get_order_for_user, load_orders_for_user
from app.services.payment_service import start_sslcommerz_payment

router = APIRouter(prefix="/api/orders", tags=["orders"])
CurrentUserDependency = Annotated[CurrentUser, Depends(require_current_user)]


@router.get("/me", response_model=list[Order])
def list_my_orders(user: CurrentUserDependency):
    return load_orders_for_user(user)


@router.get("/{order_id}", response_model=Order)
def get_my_order(order_id: str, user: CurrentUserDependency):
    return get_order_for_user(order_id, user)


@router.post("/checkout", response_model=CheckoutSession, status_code=201)
def create_checkout(checkout: CheckoutCreate, user: CurrentUserDependency):
    order = create_pending_order(checkout, user)
    payment_url = start_sslcommerz_payment(order, user.email)
    return CheckoutSession(order_id=order["id"], payment_url=payment_url)
