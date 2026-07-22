from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status

from app.api.dependencies import CurrentUser
from app.core.supabase_client import get_supabase
from app.schemas.order import CheckoutCreate, Order


def _serialize_order(order: dict) -> Order:
    items = order.pop("order_items", [])
    return Order(**order, items=items)


def load_orders_for_user(user: CurrentUser) -> list[Order]:
    response = (
        get_supabase()
        .table("orders")
        .select("*, order_items(*)")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return [_serialize_order(order) for order in response.data]


def create_pending_order(checkout: CheckoutCreate, user: CurrentUser) -> dict:
    supabase = get_supabase()
    idempotency_key = str(checkout.idempotency_key)
    existing_order = (
        supabase.table("orders")
        .select("*")
        .eq("user_id", user.id)
        .eq("idempotency_key", idempotency_key)
        .limit(1)
        .execute()
    )
    if existing_order.data:
        return existing_order.data[0]

    requested_quantities = {
        item.product_id: item.quantity for item in checkout.items
    }
    products_response = (
        supabase.table("products")
        .select("id, name, price, stock_status")
        .in_("id", list(requested_quantities))
        .execute()
    )
    products = {product["id"]: product for product in products_response.data}
    missing_products = set(requested_quantities) - set(products)
    if missing_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more products are no longer available.",
        )

    unavailable_products = [
        product["name"]
        for product in products.values()
        if product.get("stock_status") == "out_of_stock"
    ]
    if unavailable_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Out of stock: {', '.join(unavailable_products)}.",
        )

    order_items = []
    subtotal = Decimal("0")
    for product_id, quantity in requested_quantities.items():
        product = products[product_id]
        unit_price = Decimal(str(product["price"]))
        subtotal += unit_price * quantity
        order_items.append(
            {
                "product_id": product_id,
                "product_name": product["name"],
                "unit_price": float(unit_price),
                "quantity": quantity,
            }
        )

    order_response = (
        supabase.table("orders")
        .insert(
            {
                "user_id": user.id,
                "customer_name": checkout.customer_name.strip(),
                "customer_phone": checkout.customer_phone.strip(),
                "customer_address": checkout.customer_address.strip(),
                "subtotal": float(subtotal),
                "delivery_fee": 0,
                "total": float(subtotal),
                "currency": "BDT",
                "status": "pending_payment",
                "idempotency_key": idempotency_key,
            }
        )
        .execute()
    )
    order = order_response.data[0]

    for item in order_items:
        item["order_id"] = order["id"]
    supabase.table("order_items").insert(order_items).execute()
    supabase.table("payments").insert(
        {
            "order_id": order["id"],
            "provider": "sslcommerz",
            "status": "created",
            "amount": order["total"],
            "currency": order["currency"],
        }
    ).execute()
    return order


def get_order_for_user(order_id: str, user: CurrentUser) -> Order:
    response = (
        get_supabase()
        .table("orders")
        .select("*, order_items(*)")
        .eq("id", order_id)
        .eq("user_id", user.id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Order not found.")
    return _serialize_order(response.data[0])
