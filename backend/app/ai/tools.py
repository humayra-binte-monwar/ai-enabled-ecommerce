from app.schemas.ai import (
    ChatCartAction,
    ChatCartItem,
    ChatProductCard,
)
from app.services.bundle_planner_service import plan_bundle
from app.services.cart_optimizer_service import optimize_cart
from app.services.product_finder_service import find_products
from app.services.product_service import get_product_by_id, load_products

SEARCH_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "my",
    "of",
    "the",
    "to",
    "under",
    "with",
}


def product_to_chat_card(product, reason: str | None = None) -> ChatProductCard:
    return ChatProductCard(
        id=product.id,
        name=product.name,
        category=product.category,
        price=product.price,
        unit=product.unit,
        image_url=product.image_url,
        product_url=product.product_url,
        reason=reason,
    )


def search_products_tool(query: str) -> list[ChatProductCard]:
    result = find_products(query)
    return [
        ChatProductCard(
            id=product.id,
            name=product.name,
            category=product.category,
            price=product.price,
            unit=product.unit,
            image_url=product.image_url,
            product_url=product.product_url,
            reason=product.reason,
        )
        for product in result["products"]
    ]


def compare_prices_tool(query: str, limit: int = 5) -> list[ChatProductCard]:
    query_terms = [
        term
        for term in query.lower().split()
        if len(term) > 1 and term not in SEARCH_STOP_WORDS
    ]

    if not query_terms:
        return []

    products = [
        product
        for product in load_products()
        if any(
            term
            in " ".join(
                [
                    product.name,
                    product.category,
                    product.brand or "",
                    product.unit or "",
                ]
            ).lower()
            for term in query_terms
        )
    ]

    products.sort(key=lambda product: product.price)
    return [
        product_to_chat_card(product, "Sorted by lowest price")
        for product in products[:limit]
    ]


def propose_add_to_cart_tool(product_id: str, quantity: int) -> ChatCartAction | None:
    product = get_product_by_id(product_id)

    if not product:
        return None

    card = product_to_chat_card(product, "Selected for cart action")
    return ChatCartAction(
        type="add_item",
        product_id=product.id,
        product_name=product.name,
        quantity=max(1, quantity),
        requires_confirmation=True,
        message=f"Add {max(1, quantity)} x {product.name} to cart.",
        product=card,
    )


def optimize_cart_tool(items: list[ChatCartItem], goal: str | None = None) -> dict:
    return optimize_cart(items=items, goal=goal)


def plan_bundle_tool(
    budget: float,
    people: int,
    duration_days: int,
    meal_type: str,
    preference: str | None = None,
) -> dict:
    return plan_bundle(
        budget=budget,
        people=people,
        duration_days=duration_days,
        meal_type=meal_type,
        preference=preference,
    )
