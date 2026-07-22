import math
import re

from app.schemas.ai import BundlePlannerItem
from app.services.product_finder_service import get_intent_terms
from app.services.product_service import load_products

FOOD_PLAN_MEALS = {
    "baking",
    "beverage",
    "biryani",
    "breakfast",
    "cooking",
    "curry",
    "dairy",
    "dessert",
    "dinner",
    "eid",
    "healthy",
    "iftar",
    "kids",
    "lunch",
    "picnic",
    "ramadan",
    "school",
    "snacks",
    "tea",
}

NON_FOOD_TERMS = {
    "bathroom",
    "body wash",
    "clean",
    "cleaner",
    "cleaning",
    "detergent",
    "dishwash",
    "floor",
    "glass cleaner",
    "laundry",
    "liquid detergent",
    "lotion",
    "powder free",
    "rin",
    "shampoo",
    "soap",
    "tiles",
    "toilet",
    "wash",
    "wheel",
}

TERM_RULES = {
    "oil": {
        "required_any": ["oil", "soyabean", "soybean", "mustard", "rice bran", "sunflower"],
        "excluded": ["body wash", "lotion", "toilet", "cleaner", "detergent", "soap"],
    },
    "egg": {
        "required_any": ["egg loose", "egg"],
        "excluded": ["noodle", "noodles", "cake", "biscuit"],
    },
    "rice": {
        "required_any": ["rice", "chinigura", "miniket", "najir", "basmati"],
        "excluded": [],
    },
    "dal": {
        "required_any": ["dal", "lentil", "moshur", "mug", "motor"],
        "excluded": [],
    },
    "milk": {
        "required_any": ["milk"],
        "excluded": ["body milk", "lotion"],
    },
    "bread": {
        "required_any": ["bread", "bun", "loaf"],
        "excluded": [],
    },
    "flour": {
        "required_any": ["flour", "atta", "maida"],
        "excluded": [],
    },
    "atta": {
        "required_any": ["atta", "flour"],
        "excluded": [],
    },
}

MEAL_NEEDS = {
    "baby": ["baby", "diaper", "milk", "cereal", "powder", "soap", "lotion"],
    "baking": ["flour", "atta", "sugar", "butter", "milk", "chocolate", "cream"],
    "beverage": ["water", "juice", "soft drink", "cola", "tea", "coffee", "milk"],
    "biryani": ["rice", "oil", "ghee", "spice", "masala", "onion", "salt"],
    "breakfast": ["milk", "bread", "egg", "tea", "coffee", "cereal", "oats", "butter"],
    "cleaning": ["detergent", "soap", "dishwash", "cleaner", "toilet", "tissue"],
    "cooking": ["rice", "dal", "oil", "salt", "spice", "masala", "onion", "garlic"],
    "curry": ["oil", "spice", "masala", "onion", "garlic", "ginger", "salt"],
    "dairy": ["milk", "powder", "cheese", "butter", "yogurt", "cream"],
    "dessert": ["milk", "sugar", "semai", "cream", "chocolate", "cake", "biscuit"],
    "dinner": ["rice", "dal", "oil", "spice", "vegetable", "egg", "fish", "chicken"],
    "eid": ["rice", "semai", "milk", "sugar", "ghee", "spice", "oil"],
    "essentials": ["rice", "dal", "oil", "salt", "sugar", "flour", "soap", "milk"],
    "family": ["rice", "dal", "oil", "milk", "egg", "bread", "soap", "detergent"],
    "healthy": ["dal", "vegetable", "egg", "milk", "oats", "fruit", "atta"],
    "iftar": ["dates", "juice", "chola", "oil", "puffed rice", "semai", "fruit"],
    "kids": ["milk", "juice", "biscuit", "cake", "chocolate", "noodles", "cereal"],
    "lunch": ["rice", "dal", "oil", "spice", "vegetable", "fish", "chicken", "egg"],
    "monthly": ["rice", "dal", "oil", "salt", "sugar", "flour", "soap", "detergent"],
    "personal": ["soap", "shampoo", "toothpaste", "brush", "lotion", "powder"],
    "picnic": ["chips", "biscuit", "juice", "water", "cake", "noodles", "chanachur"],
    "ramadan": ["dates", "juice", "chola", "oil", "puffed rice", "semai", "milk"],
    "school": ["biscuit", "juice", "cake", "bread", "chocolate", "water"],
    "snacks": ["biscuit", "chips", "juice", "cake", "chanachur", "noodles", "chocolate"],
    "tea": ["tea", "milk", "sugar", "biscuit", "cake"],
    "weekly": ["rice", "dal", "oil", "milk", "egg", "bread", "vegetable"],
}

INTENT_ONLY_TERMS = set(MEAL_NEEDS) - {"snacks", "tea"}

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


def get_package_size(product_name: str) -> tuple[float, str] | None:
    name = product_name.lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|gm|g|ltr|l|ml)", name)

    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit == "kg":
        return amount, "kg"
    if unit in {"gm", "g"}:
        return amount / 1000, "kg"
    if unit in {"ltr", "l"}:
        return amount, "l"
    if unit == "ml":
        return amount / 1000, "l"

    return None


def estimate_quantity(product_name: str, term: str, people: int, duration_days: int) -> tuple[int, str]:
    searchable_text = f"{product_name} {term}".lower()
    scale = max(1, people) * max(1, duration_days) / 4

    package_size = get_package_size(product_name)

    if term == "oil" and package_size and package_size[1] == "l":
        needed_liters = 0.25 * scale
        quantity = math.ceil(needed_liters / package_size[0])
        return max(1, quantity), "about 250ml cooking oil per person for 4 days"

    for keyword, (base_quantity, explanation) in QUANTITY_RULES.items():
        if keyword in searchable_text:
            if keyword in {"salt", "spice", "masala", "tea"}:
                return 1, explanation

            quantity = round(base_quantity * scale)
            return max(1, quantity), explanation

    quantity = max(1, round(scale / 2))
    return quantity, "estimated from household size and shopping duration"


def is_food_plan(query: str) -> bool:
    query_lower = query.lower()
    asks_for_non_food = any(
        word in query_lower for word in ["cleaning", "personal", "toiletries", "bathroom"]
    )
    asks_for_food = any(meal in query_lower for meal in FOOD_PLAN_MEALS)

    return asks_for_food and not asks_for_non_food


def product_text(product) -> str:
    return " ".join(
        [
            product.name,
            product.category,
            product.brand or "",
            product.unit or "",
        ]
    ).lower()


def matches_term(product, term: str, food_only: bool) -> bool:
    searchable_text = product_text(product)

    if food_only and any(blocked in searchable_text for blocked in NON_FOOD_TERMS):
        return False

    rule = TERM_RULES.get(term)
    if rule:
        if any(blocked in searchable_text for blocked in rule["excluded"]):
            return False

        return any(required in searchable_text for required in rule["required_any"])

    return term in searchable_text


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
    food_only = is_food_plan(query)

    for meal, needs in MEAL_NEEDS.items():
        if meal in query.lower():
            terms.extend(needs)

    if food_only:
        terms = [term for term in terms if term not in INTENT_ONLY_TERMS]

    terms = list(dict.fromkeys(terms))

    selected_items = []
    used_product_ids = set()
    estimated_total = 0.0

    for term in terms:
        candidates = []

        for product in products:
            if matches_term(product, term, food_only) and product.id not in used_product_ids:
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
                        reason=f"Suggested for {term}; {quantity_reason}{budget_note}",
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
