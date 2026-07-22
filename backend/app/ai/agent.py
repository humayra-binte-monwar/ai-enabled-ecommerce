import re

from app.ai.guardrails import health_disclaimer, is_health_question
from app.ai.prompts import FALLBACK_FOLLOW_UPS
from app.ai.tools import (
    compare_prices_tool,
    optimize_cart_tool,
    plan_bundle_tool,
    propose_add_to_cart_tool,
    search_products_tool,
)
from app.core.settings import get_settings
from app.schemas.ai import ChatCitation, ChatRequest, ChatResponse

try:
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False


def extract_quantity(message: str) -> int:
    match = re.search(r"\b(\d+)\b", message)
    return int(match.group(1)) if match else 1


def extract_budget(message: str) -> float | None:
    match = re.search(r"(?:under|below|within|max|maximum)\s*(?:tk|taka)?\s*(\d+)", message.lower())
    return float(match.group(1)) if match else None


def looks_like_cart_add(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["add", "put"]) and "cart" in message_lower


def looks_like_bundle_request(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["bundle", "basket", "meal plan", "recipe"])


def looks_like_cart_review(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["optimize", "review", "healthier", "save", "reduce"]) and "cart" in message_lower


def should_compare_prices(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["cheapest", "lowest price", "compare", "best value"])


def clean_search_query(message: str) -> str:
    cleaned = message.lower()
    for term in ["add", "put", "to my cart", "cart", "cheapest", "lowest price", "compare", "best value"]:
        cleaned = cleaned.replace(term, " ")
    cleaned = re.sub(r"\b\d+\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or message


def run_langchain_placeholder(request: ChatRequest) -> ChatResponse | None:
    settings = get_settings()

    if not settings.ai_agent_enabled or not settings.openai_api_key or not LANGCHAIN_AVAILABLE:
        return None

    # This keeps the first implementation safe: LangChain is configured here,
    # while deterministic tools still handle product/cart grounding below.
    _llm = ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )
    return None


def run_chat(request: ChatRequest) -> ChatResponse:
    langchain_response = run_langchain_placeholder(request)

    if langchain_response:
        return langchain_response

    message = request.message.strip()
    query = clean_search_query(message)
    tools_used = []
    products = []
    cart_actions = []
    intent = "product_search"

    if looks_like_cart_review(message):
        intent = "cart_optimizer"
        tools_used.append("optimize_cart")
        optimized = optimize_cart_tool(request.cart_items, goal=message)
        return ChatResponse(
            message=optimized["summary"],
            intent=intent,
            follow_up_suggestions=FALLBACK_FOLLOW_UPS,
            tools_used=tools_used,
            fallback=True,
        )

    if looks_like_bundle_request(message):
        intent = "bundle_planner"
        budget = extract_budget(message) or 1500
        tools_used.append("plan_bundle")
        bundle = plan_bundle_tool(
            budget=budget,
            people=2,
            duration_days=3,
            meal_type=query,
        )
        for bundle_item in bundle["items"][:4]:
            matches = search_products_tool(bundle_item.name)
            if matches:
                products.append(matches[0])

        return ChatResponse(
            message=f"{bundle['summary']} Estimated total: Tk {bundle['estimated_total']}.",
            intent=intent,
            products=products,
            citations=[
                ChatCitation(product_id=product.id, source_url=product.product_url)
                for product in products
            ],
            follow_up_suggestions=["Add this bundle to my cart", "Make it cheaper", "Make it healthier"],
            tools_used=tools_used,
            fallback=True,
        )

    if should_compare_prices(message):
        intent = "price_compare"
        tools_used.append("compare_prices")
        products = compare_prices_tool(query)
    else:
        tools_used.append("search_products")
        products = search_products_tool(message)

    if looks_like_cart_add(message) and products:
        intent = "cart_add"
        tools_used.append("propose_add_to_cart")
        action = propose_add_to_cart_tool(products[0].id, extract_quantity(message))
        if action:
            cart_actions.append(action)

    if is_health_question(message):
        intent = "health_info"
        prefix = f"{health_disclaimer(message)} "
    else:
        prefix = ""

    if products:
        message_text = f"{prefix}I found {len(products)} matching product(s)."
        if cart_actions:
            message_text += " I prepared a cart action for you to confirm."
    else:
        message_text = (
            f"{prefix}I could not find a strong catalog match yet. Try asking for a product, "
            "category, budget, or cart goal."
        )

    return ChatResponse(
        message=message_text,
        intent=intent,
        products=products,
        cart_actions=cart_actions,
        citations=[
            ChatCitation(product_id=product.id, source_url=product.product_url)
            for product in products
        ],
        follow_up_suggestions=FALLBACK_FOLLOW_UPS,
        tools_used=tools_used,
        fallback=True,
    )
