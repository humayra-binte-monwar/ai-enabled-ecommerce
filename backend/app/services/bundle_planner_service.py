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
            if estimated_total + candidate.price <= budget:
                selected_items.append(
                    BundlePlannerItem(
                        id=candidate.id,
                        name=candidate.name,
                        category=candidate.category,
                        price=candidate.price,
                        unit=candidate.unit,
                        image_url=candidate.image_url,
                        product_url=candidate.product_url,
                        reason=f"Added for {term}",
                    )
                )
                used_product_ids.add(candidate.id)
                estimated_total += candidate.price
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