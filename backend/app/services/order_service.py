from app.core.supabase_client import get_supabase
from app.schemas.order import Order, OrderCreate


def load_orders() -> list[Order]:
    supabase = get_supabase()

    response = (
        supabase.table("orders")
        .select("*, order_items(*)")
        .order("created_at", desc=True)
        .execute()
    )

    orders = []
    for item in response.data:
        order_items = item.pop("order_items", [])
        orders.append(Order(**item, items=order_items))

    return orders


def create_order(order_data: OrderCreate) -> Order:
    supabase = get_supabase()

    order_response = (
        supabase.table("orders")
        .insert(
            {
            "customer_name": order_data.customer_name,
            "customer_phone": order_data.customer_phone,
            "customer_address": order_data.customer_address,
            "total": order_data.total,
            "status": "confirmed",
            "user_id": order_data.user_id,
            "user_email": order_data.user_email,
            "payment_method": order_data.payment_method,
            "payment_status": order_data.payment_status,
            }
        )
        .execute()
    )

    order = order_response.data[0]

    order_items = [
        {
            "order_id": order["id"],
            "product_id": item.product_id,
            "name": item.name,
            "price": item.price,
            "quantity": item.quantity,
        }
        for item in order_data.items
    ]

    if order_items:
        supabase.table("order_items").insert(order_items).execute()

    return Order(
        id=order["id"],
        customer_name=order["customer_name"],
        customer_phone=order["customer_phone"],
        customer_address=order["customer_address"],
        total=float(order["total"]),
        status=order["status"],
        created_at=order["created_at"],
        items=order_data.items,
        user_id=order.get("user_id"),
        user_email=order.get("user_email"),
        payment_method=order.get("payment_method", "mock_card"),
        payment_status=order.get("payment_status", "paid_demo"),
    )
