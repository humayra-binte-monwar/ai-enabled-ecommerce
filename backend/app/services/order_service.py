import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.order import Order, OrderCreate

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ORDERS_FILE = PROJECT_ROOT / "data" / "processed" / "orders.json"


def load_orders() -> list[Order]:
    if not ORDERS_FILE.exists():
        return []

    with ORDERS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [Order(**item) for item in data]


def save_orders(orders: list[Order]) -> None:
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with ORDERS_FILE.open("w", encoding="utf-8") as file:
        json.dump([order.model_dump() for order in orders], file, indent=2)


def create_order(order_data: OrderCreate) -> Order:
    orders = load_orders()

    order = Order(
        id=str(uuid4()),
        status="confirmed",
        created_at=datetime.now(timezone.utc).isoformat(),
        **order_data.model_dump(),
    )

    orders.append(order)
    save_orders(orders)

    return order