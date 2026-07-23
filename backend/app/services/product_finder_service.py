import re

from app.schemas.ai import ProductFinderProduct
from app.services.product_service import load_products

INTENT_KEYWORDS = {
    "affordable": ["rice", "dal", "oil", "salt", "sugar", "atta", "noodles"],
    "baby": ["baby", "diaper", "powder", "lotion", "soap", "milk", "cereal"],
    "baking": ["flour", "atta", "sugar", "butter", "milk", "powder", "chocolate"],
    "bbq": ["chicken", "beef", "spice", "masala", "sauce", "oil", "coal"],
    "beverage": ["water", "juice", "soft drink", "cola", "tea", "coffee"],
    "biryani": ["rice", "oil", "spice", "masala", "onion", "salt", "ghee"],
    "breakfast": ["milk", "bread", "egg", "cereal", "butter", "tea", "coffee", "oats"],
    "cleaning": ["detergent", "soap", "dishwash", "cleaner", "toilet", "floor"],
    "cooking": ["rice", "oil", "salt", "spice", "dal", "flour", "onion", "garlic"],
    "curry": ["oil", "spice", "masala", "onion", "garlic", "ginger", "salt"],
    "dairy": ["milk", "cheese", "butter", "yogurt", "cream", "powder"],
    "dessert": ["sugar", "milk", "cream", "chocolate", "cake", "biscuit"],
    "dinner": ["rice", "dal", "oil", "spice", "fish", "chicken", "vegetable"],
    "eid": ["rice", "semai", "milk", "sugar", "spice", "oil", "ghee"],
    "essentials": ["rice", "dal", "oil", "salt", "sugar", "flour", "soap"],
    "family": ["rice", "oil", "dal", "milk", "egg", "bread", "soap"],
    "frozen": [
        "kazi",
        "chicken strip",
        "chicken strips",
        "nugget",
        "nuggets",
        "sausage",
        "paratha",
        "fries",
        "french fry",
        "frozen",
    ],
    "healthy": ["dal", "vegetable", "egg", "milk", "oats", "fruit", "atta"],
    "iftar": ["dates", "juice", "chola", "oil", "puffed rice", "noodles", "fruit"],
    "kids": ["milk", "juice", "biscuit", "cake", "chocolate", "noodles", "cereal"],
    "kitchen": ["rice", "oil", "salt", "spice", "masala", "flour", "sugar"],
    "lunch": ["rice", "dal", "oil", "spice", "vegetable", "fish", "chicken"],
    "meal": ["rice", "dal", "oil", "spice", "egg", "vegetable", "atta"],
    "personal": ["soap", "shampoo", "toothpaste", "brush", "lotion", "powder"],
    "pet": ["cat", "dog", "pet", "food"],
    "picnic": ["chips", "biscuit", "juice", "water", "cake", "noodles", "snacks"],
    "ramadan": ["dates", "juice", "chola", "oil", "puffed rice", "semai", "milk"],
    "school": ["biscuit", "juice", "cake", "bread", "chocolate", "water"],
    "snacks": ["chips", "biscuit", "cake", "noodles", "chanachur", "juice", "chocolate"],
    "tea": ["tea", "milk", "sugar", "biscuit", "cake"],
    "toiletries": ["soap", "shampoo", "toothpaste", "brush", "tissue", "lotion"],
}

QUERY_SYNONYMS = {
    "bathroom": "toiletries",
    "cheap": "affordable",
    "children": "kids",
    "cook": "cooking",
    "groceries": "essentials",
    "grocery": "essentials",
    "freezer": "frozen",
    "frozen food": "frozen",
    "frozen foods": "frozen",
    "kid": "kids",
    "low": "affordable",
    "party": "picnic",
    "school lunch": "school",
    "value": "affordable",
}

STOP_WORDS = {
    "about",
    "below",
    "best",
    "budget",
    "find",
    "for",
    "foods",
    "give",
    "good",
    "items",
    "looking",
    "max",
    "maximum",
    "need",
    "show",
    "some",
    "taka",
    "that",
    "there",
    "under",
    "want",
    "what",
    "with",
    "within",
    "you",
}

NON_FOOD_TERMS = {
    "cleaner",
    "detergent",
    "dishwash",
    "floor",
    "lotion",
    "soap",
    "toilet",
    "wash",
}

NON_FOOD_CATEGORIES = {
    "cleaning",
    "personal care",
    "storage & containers",
}

FOOD_INTENTS = {
    "baking",
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
    "meal",
    "picnic",
    "ramadan",
    "school",
    "snacks",
    "tea",
}


def extract_budget(query: str) -> float | None:
    match = re.search(r"(?:under|below|within|max|maximum)\s*(?:tk|taka)?\s*(\d+)", query)
    if not match:
        match = re.search(r"(\d+)\s*(?:tk|taka)", query)

    if not match:
        return None

    return float(match.group(1))


def get_intent_terms(query: str) -> list[str]:
    query_lower = query.lower()
    terms = []

    for phrase, intent in QUERY_SYNONYMS.items():
        if phrase in query_lower:
            terms.append(intent)
            terms.extend(INTENT_KEYWORDS.get(intent, []))

    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in query_lower:
            terms.extend(keywords)

    direct_words = [
        word
        for word in re.findall(r"[a-zA-Z]+", query_lower)
        if len(word) > 2 and word not in STOP_WORDS
    ]

    terms.extend(direct_words)

    return list(dict.fromkeys(terms))


def is_food_query(query: str) -> bool:
    query_lower = query.lower()
    return any(intent in query_lower for intent in FOOD_INTENTS)


def term_matches_product(term: str, searchable_text: str) -> bool:
    if term == "egg" and "noodle" in searchable_text:
        return False

    if term == "milk" and any(blocked in searchable_text for blocked in ["body milk", "lotion"]):
        return False

    if term == "oil" and any(
        blocked in searchable_text
        for blocked in ["body wash", "cleaner", "detergent", "soap", "toilet"]
    ):
        return False

    return term in searchable_text


def find_products(query: str) -> dict:
    products = load_products()
    budget = extract_budget(query.lower())
    terms = get_intent_terms(query)
    food_query = is_food_query(query)

    scored_products = []

    for product in products:
        searchable_text = " ".join(
            [
                product.name,
                product.category,
                product.normalized_category or "",
                product.product_type or "",
                " ".join(product.tags),
                product.brand or "",
                product.unit or "",
            ]
        ).lower()

        product_categories = {
            product.category.lower(),
            (product.normalized_category or "").lower(),
        }
        if food_query and (
            any(term in searchable_text for term in NON_FOOD_TERMS)
            or product_categories.intersection(NON_FOOD_CATEGORIES)
        ):
            continue

        score = 0
        matched_terms = []

        for term in terms:
            if term_matches_product(term, searchable_text):
                score += 2
                matched_terms.append(term)

        if terms and not matched_terms:
            continue

        if budget and product.price <= budget:
            score += 1

        if budget and product.price > budget:
            score -= 2

        if score > 0 and matched_terms:
            scored_products.append((score, matched_terms, product))

    scored_products.sort(key=lambda item: (-item[0], item[2].price))

    top_matches = scored_products[:8]

    result_products = [
        ProductFinderProduct(
            id=product.id,
            name=product.name,
            category=product.category,
            price=product.price,
            unit=product.unit,
            image_url=product.image_url,
            product_url=product.product_url,
            tags=product.tags,
            normalized_category=product.normalized_category,
            product_type=product.product_type,
            reason=(
                f"Matched: {', '.join(matched_terms)}"
                if matched_terms
                else "Matched catalog intent"
            ),
        )
        for _score, matched_terms, product in top_matches
    ]

    if not result_products:
        return {
            "summary": "I could not find strong matches. Try asking for a product, category, or budget.",
            "products": [],
        }

    budget_text = f" under Tk {budget:.0f}" if budget else ""
    return {
        "summary": f"Found {len(result_products)} product matches{budget_text}.",
        "products": result_products,
    }
