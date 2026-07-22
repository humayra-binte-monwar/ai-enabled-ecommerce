from app.schemas.ai import CartOptimizerSuggestion
from app.services.product_service import load_products

ESSENTIAL_TERMS = ["rice", "dal", "oil", "egg", "milk", "salt", "sugar"]
NON_FOOD_TERMS = ["cleaner", "detergent", "toilet", "soap", "shampoo", "wash"]
HEALTHIER_TERMS = ["oats", "atta", "dal", "egg", "milk", "rice bran", "water"]
BUDGET_GOALS = ["budget", "cheap", "save"]

STAPLE_GROUPS = {
    "atta": ["atta", "flour", "maida"],
    "dal": ["dal", "lentil", "moshur", "mug", "motor"],
    "noodles": ["noodle", "noodles"],
    "egg": ["egg loose"],
    "garlic": ["garlic", "roshun"],
    "ginger": ["ginger", "ada"],
    "milk": ["milk"],
    "oil": ["oil", "soyabean", "soybean", "mustard", "rice bran", "sunflower"],
    "onion": ["onion", "piyaj"],
    "potato": ["potato", "alu"],
    "rice": ["rice", "chinigura", "miniket", "najir", "basmati"],
    "salt": ["salt"],
    "sugar": ["sugar"],
    "vegetable": ["vegetable", "tomato", "carrot", "cucumber", "begun"],
}

def normalize(text: str | None) -> str:
    return (text or "").lower()


def product_text(product) -> str:
    return " ".join(
        [
            product.name,
            product.category,
            product.brand or "",
            product.unit or "",
        ]
    ).lower()


def cart_text(items: list) -> str:
    return " ".join(f"{item.name} {item.category}" for item in items).lower()


def find_best_product(term: str, excluded_ids: set[str]) -> object | None:
    group = STAPLE_GROUPS.get(term, [term])
    matches = [
        product
        for product in load_products()
        if product.id not in excluded_ids
        and any(group_term in product_text(product) for group_term in group)
        and not any(blocked in product_text(product) for blocked in NON_FOOD_TERMS)
        and not (term == "egg" and "noodle" in product_text(product))
    ]

    matches.sort(key=lambda product: product.price)
    return matches[0] if matches else None


def get_product_group(name: str) -> tuple[str, list[str]] | None:
    name_lower = normalize(name)

    if "noodle" in name_lower:
        return "noodles", STAPLE_GROUPS["noodles"]

    for group, terms in STAPLE_GROUPS.items():
        if any(term in name_lower for term in terms):
            return group, terms

    return None


def find_cheaper_alternative(cart_item, excluded_ids: set[str]) -> object | None:
    group = get_product_group(cart_item.name)

    if not group:
        return None

    _group_name, group_terms = group
    matches = [
        product
        for product in load_products()
        if product.id not in excluded_ids
        and product.price < cart_item.price
        and any(term in product_text(product) for term in group_terms)
        and not any(term in product_text(product) for term in NON_FOOD_TERMS)
    ]

    matches.sort(key=lambda product: product.price)
    return matches[0] if matches else None


def make_product_suggestion(suggestion_type: str, message: str, product) -> CartOptimizerSuggestion:
    return CartOptimizerSuggestion(
        type=suggestion_type,
        message=message,
        product_id=product.id,
        product_name=product.name,
        category=product.category,
        price=product.price,
        unit=product.unit,
        image_url=product.image_url,
        product_url=product.product_url,
    )


def optimize_cart(items: list, goal: str | None = None) -> dict:
    if not items:
        return {
            "summary": "Add products to your cart first, then I can optimize it.",
            "cart_total": 0,
            "suggestions": [],
        }

    goal_text = normalize(goal)
    wants_budget_help = any(goal_word in goal_text for goal_word in BUDGET_GOALS)
    cart_total = sum(item.price * item.quantity for item in items)
    current_text = cart_text(items)
    current_ids = {item.product_id for item in items}
    suggestions = []
    suggested_product_ids = set()
    found_savings_alternative = False

    if wants_budget_help:
        for item in sorted(items, key=lambda cart_item: cart_item.price, reverse=True):
            alternative = find_cheaper_alternative(item, current_ids | suggested_product_ids)

            if alternative:
                found_savings_alternative = True
                savings = item.price - alternative.price
                suggestions.append(
                    make_product_suggestion(
                        "save_money",
                        f"Cheaper alternative for {item.name}: compare this option and save about Tk {savings:.0f} per item.",
                        alternative,
                    )
                )
                suggested_product_ids.add(alternative.id)

        if not found_savings_alternative:
            suggestions.append(
                CartOptimizerSuggestion(
                    type="save_money",
                    message="I did not find cheaper same-type substitutes for the items already in your cart.",
                )
            )

    for term in ESSENTIAL_TERMS:
        if len(suggestions) >= 5:
            break

        if term in current_text:
            continue

        product = find_best_product(term, current_ids | suggested_product_ids)

        if product:
            suggestions.append(
                make_product_suggestion(
                    "missing_essential",
                    f"You may be missing {term}. This is a low-price option to complete the basket.",
                    product,
                )
            )
            suggested_product_ids.add(product.id)

    if "healthy" in goal_text or "balanced" in goal_text:
        has_healthy_item = any(term in current_text for term in HEALTHIER_TERMS)

        if not has_healthy_item:
            product = next(
                (
                    find_best_product(term, current_ids)
                    for term in HEALTHIER_TERMS
                    if find_best_product(term, current_ids)
                ),
                None,
            )

            if product:
                suggestions.append(
                    make_product_suggestion(
                        "healthier_choice",
                        "Your cart could use a more balanced staple for the health goal.",
                        product,
                    )
                )

    non_food_count = sum(
        1
        for item in items
        if any(term in normalize(item.name) for term in NON_FOOD_TERMS)
    )

    if non_food_count and "meal" in goal_text:
        suggestions.append(
            CartOptimizerSuggestion(
                type="cart_balance",
                message="This cart includes cleaning or personal-care items, but your goal sounds meal-focused.",
            )
        )

    if not suggestions:
        suggestions.append(
            CartOptimizerSuggestion(
                type="cart_balance",
                message="Your cart already looks focused. You can continue to checkout.",
            )
        )

    return {
        "summary": f"Reviewed {len(items)} cart item(s), total Tk {cart_total:.0f}.",
        "cart_total": round(cart_total, 2),
        "suggestions": suggestions[:5],
    }
