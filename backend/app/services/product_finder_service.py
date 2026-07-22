import re

from app.schemas.ai import ProductFinderProduct
from app.services.product_service import load_products

INTENT_KEYWORDS = {
    "breakfast": ["milk", "bread", "egg", "cereal", "butter", "tea", "coffee"],
    "snacks": ["chips", "biscuit", "cake", "noodles", "chanachur", "juice"],
    "kids": ["milk", "juice", "biscuit", "cake", "chocolate", "noodles"],
    "biryani": ["rice", "oil", "spice", "masala", "onion", "salt"],
    "cooking": ["rice", "oil", "salt", "spice", "dal", "flour"],
    "healthy": ["dal", "vegetable", "egg", "milk", "oats", "fruit"],
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

    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in query_lower:
            terms.extend(keywords)

    direct_words = [
        word
        for word in re.findall(r"[a-zA-Z]+", query_lower)
        if len(word) > 2 and word not in {"under", "below", "within", "taka", "max", "maximum"}
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