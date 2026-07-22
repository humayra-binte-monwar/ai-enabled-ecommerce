from app.schemas.ai import BundlePlannerItem
from app.services.product_finder_service import get_intent_terms
from app.services.product_service import load_products

MEAL_NEEDS = {
    "breakfast": ["milk", "bread", "egg", "tea", "coffee", "cereal", "oats"],
    "lunch": ["rice", "dal", "oil", "spice", "vegetable", "fish", "chicken"],
    "dinner": ["rice", "dal", "oil", "spice", "vegetable", "egg"],
    "snacks": ["biscuit", "chips", "juice", "cake", "chanachur", "noodles"],
    "essentials": ["rice", "dal", "oil", "salt", "sugar", "flour", "soap"],
}

QUANTITY_RULES = {
    "rice": (1.0, "about 1kg rice per person for 4 days"),
    "dal": (0.35, "about 350g dal per person for 4 days"),
    "flour": (0.5, "about 500g flour/atta per person for 4 days"),
    "atta": (0.5, "about 500g atta per person for 4 days"),
    "oil": (0.25, "about 250ml cooking oil per person for 4 days"),
    "egg": (3.0, "about 3 eggs per person for 4 days"),
    "milk": (1.0, "about 1 pack of milk per person for 4 days"),
    "bread": (1.0, "about 1 loaf/pack for every 2 people"),
    "biscuit": (1.0, "about 1 pack for every 2 people"),
    "snacks": (1.0, "about 1 pack for every 2 people"),
    "salt": (1.0, "1 pack is usually enough for a small household"),
    "sugar": (0.25, "about 250g sugar per person for 4 days"),
    "tea": (0.2, "1 small tea pack usually covers several days"),
    "spice": (1.0, "1 spice pack is usually enough"),
    "masala": (1.0, "1 masala pack is usually enough"),
    "soap": (1.0, "about 1 item for every 2 people"),
}


def estimate_quantity(product_name: str, term: str, people: int, duration_days: int) -> tuple[int, str]:
    searchable_text = f"{product_name} {term}".lower()
    scale = max(1, people) * max(1, duration_days) / 4

    for keyword, (base_quantity, explanation) in QUANTITY_RULES.items():
        if keyword in searchable_text:
            if keyword in {"salt", "spice", "masala", "tea"}:
                return 1, explanation

            quantity = round(base_quantity * scale)
            return max(1, quantity), explanation

    quantity = max(1, round(scale / 2))
    return quantity, "estimated from household size and shopping duration"


def plan_bundle(
    budget: float,
    people: int,
    duration_days: int,
    meal_type: str,
    preference: str | None = None,
) -> dict:
    products = load_products()
    query = f"{meal_type} {preference or ''}"
    terms = get_intent_terms(query)

    for meal, needs in MEAL_NEEDS.items():
        if meal in query.lower():
            terms.extend(needs)

    terms = list(dict.fromkeys(terms))

    selected_items = []
    used_product_ids = set()
    estimated_total = 0.0

    for term in terms:
        candidates = []

        for product in products:
            searchable_text = " ".join(
                [
                    product.name,
                    product.category,
                    product.brand or "",
                    product.unit or "",
                ]
            ).lower()

            if term in searchable_text and product.id not in used_product_ids:
                candidates.append(product)

        candidates.sort(key=lambda product: product.price)

        for candidate in candidates:
            recommended_quantity, quantity_reason = estimate_quantity(
                candidate.name,
                term,
                people,
                duration_days,
            )
            quantity = recommended_quantity
            line_total = candidate.price * quantity

            while quantity > 1 and estimated_total + line_total > budget:
                quantity -= 1
                line_total = candidate.price * quantity

            if estimated_total + line_total <= budget:
                budget_note = ""
                if quantity < recommended_quantity:
                    budget_note = (
                        f"; budget-fit suggestion reduced from {recommended_quantity} to {quantity}"
                    )

                selected_items.append(
                    BundlePlannerItem(
                        id=candidate.id,
                        name=candidate.name,
                        category=candidate.category,
                        price=candidate.price,
                        unit=candidate.unit,
                        image_url=candidate.image_url,
                        product_url=candidate.product_url,
                        recommended_quantity=recommended_quantity,
                        suggested_quantity=quantity,
                        reason=f"Added for {term}; {quantity_reason}{budget_note}",
                    )
                )
                used_product_ids.add(candidate.id)
                estimated_total += line_total
                break

    if not selected_items:
        return {
            "summary": "I could not build a bundle within this budget. Try increasing the budget or using a broader meal type.",
            "estimated_total": 0,
            "remaining_budget": budget,
            "items": [],
        }

    return {
        "summary": (
            f"Built a grocery bundle for {people} people over "
            f"{duration_days} day(s), focused on {meal_type}."
        ),
        "estimated_total": round(estimated_total, 2),
        "remaining_budget": round(budget - estimated_total, 2),
        "items": selected_items,
    }
