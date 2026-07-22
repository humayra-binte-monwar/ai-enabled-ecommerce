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
    "under",
    "want",
    "with",
    "within",
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


def find_products(query: str) -> dict:
    products = load_products()
    budget = extract_budget(query.lower())
    terms = get_intent_terms(query)

    scored_products = []

    for product in products:
        searchable_text = " ".join(
            [
                product.name,
                product.category,
                product.brand or "",
                product.unit or "",
            ]
        ).lower()

        score = 0
        matched_terms = []

        for term in terms:
            if term in searchable_text:
                score += 2
                matched_terms.append(term)

        if budget and product.price <= budget:
            score += 1

        if budget and product.price > budget:
            score -= 2

        if score > 0:
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
            reason=(
                f"Matched: {', '.join(matched_terms)}"
                if matched_terms
                else "Fits your budget"
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
