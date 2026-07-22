import re
import json

from app.ai.guardrails import health_disclaimer, is_health_question
from app.ai.prompts import CHAT_SYNTHESIS_PROMPT, FALLBACK_FOLLOW_UPS, SYSTEM_PROMPT
from app.ai.tools import (
    compare_prices_tool,
    optimize_cart_tool,
    plan_bundle_tool,
    propose_add_to_cart_tool,
    search_products_tool,
)
from app.core.settings import get_settings
from app.schemas.ai import ChatCartAction, ChatCitation, ChatProductCard, ChatRequest, ChatResponse

try:
    from langchain_openai import ChatOpenAI

    LANGCHAIN_AVAILABLE = True
    LANGCHAIN_IMPORT_ERROR = ""
except ImportError:
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_IMPORT_ERROR = "Could not import langchain_openai"
except Exception as error:
    ChatOpenAI = None
    LANGCHAIN_AVAILABLE = False
    LANGCHAIN_IMPORT_ERROR = str(error)


def extract_quantity(message: str) -> int:
    match = re.search(r"\b(\d+)\b", message)
    return int(match.group(1)) if match else 1


def extract_budget(message: str) -> float | None:
    match = re.search(r"(?:under|below|within|max|maximum)\s*(?:tk|taka)?\s*(\d+)", message.lower())
    return float(match.group(1)) if match else None


def looks_like_cart_add(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["add", "put", "buy"])


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
    removable_phrases = [
        "add",
        "put",
        "to my cart",
        "to cart",
        "my cart",
        "cart",
        "cheapest",
        "lowest price",
        "compare",
        "best value",
        "the",
        "of",
        "a",
        "an",
        "my",
        "for",
        "under",
        "within",
        "below",
        "taka",
        "tk",
        "please",
    ]
    for term in removable_phrases:
        cleaned = cleaned.replace(term, " ")
    cleaned = re.sub(r"\b\d+\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or message


def get_llm_client():
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if not settings.ai_agent_enabled or not LANGCHAIN_AVAILABLE:
        return None

    if provider == "groq" and settings.groq_api_key:
        return ChatOpenAI(
            model=settings.groq_chat_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0.2,
        )

    if provider == "xai" and settings.xai_api_key:
        return ChatOpenAI(
            model=settings.xai_chat_model,
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
            temperature=0.2,
        )

    if provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_chat_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.2,
        )

    return None


def products_for_prompt(products: list[ChatProductCard]) -> list[dict]:
    return [
        {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "unit": product.unit,
            "reason": product.reason,
        }
        for product in products[:5]
    ]


def cart_actions_for_prompt(cart_actions: list[ChatCartAction]) -> list[dict]:
    return [
        {
            "type": action.type,
            "product_id": action.product_id,
            "product_name": action.product_name,
            "quantity": action.quantity,
            "requires_confirmation": action.requires_confirmation,
            "message": action.message,
        }
        for action in cart_actions
    ]


def synthesize_with_llm(
    user_message: str,
    intent: str,
    default_message: str,
    products: list[ChatProductCard],
    cart_actions: list[ChatCartAction],
    tools_used: list[str],
) -> tuple[str, bool]:
    llm = get_llm_client()

    if not llm:
        return default_message, True

    prompt_payload = {
        "user_message": user_message,
        "detected_intent": intent,
        "tools_used": tools_used,
        "default_message": default_message,
        "products": products_for_prompt(products),
        "cart_actions": cart_actions_for_prompt(cart_actions),
    }

    try:
        response = llm.invoke(
            [
                ("system", SYSTEM_PROMPT),
                ("system", CHAT_SYNTHESIS_PROMPT),
                ("user", json.dumps(prompt_payload)),
            ]
        )
    except Exception:
        return default_message, True

    return str(response.content), False


def run_chat(request: ChatRequest) -> ChatResponse:
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
        for suggestion in optimized["suggestions"]:
            if suggestion.product_name:
                matches = search_products_tool(suggestion.product_name)
                if matches:
                    products.append(matches[0])

        default_message = optimized["summary"]
        response_message, used_fallback = synthesize_with_llm(
            user_message=message,
            intent=intent,
            default_message=default_message,
            products=products,
            cart_actions=cart_actions,
            tools_used=tools_used,
        )

        return ChatResponse(
            message=response_message,
            intent=intent,
            products=products,
            citations=[
                ChatCitation(product_id=product.id, source_url=product.product_url)
                for product in products
            ],
            follow_up_suggestions=FALLBACK_FOLLOW_UPS,
            tools_used=tools_used,
            fallback=used_fallback,
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

        default_message = f"{bundle['summary']} Estimated total: Tk {bundle['estimated_total']}."
        response_message, used_fallback = synthesize_with_llm(
            user_message=message,
            intent=intent,
            default_message=default_message,
            products=products,
            cart_actions=cart_actions,
            tools_used=tools_used,
        )

        return ChatResponse(
            message=response_message,
            intent=intent,
            products=products,
            citations=[
                ChatCitation(product_id=product.id, source_url=product.product_url)
                for product in products
            ],
            follow_up_suggestions=["Add this bundle to my cart", "Make it cheaper", "Make it healthier"],
            tools_used=tools_used,
            fallback=used_fallback,
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
        default_message = f"{prefix}I found {len(products)} matching product(s)."
        if cart_actions:
            default_message += " I prepared a cart action for you to confirm."
    else:
        default_message = (
            f"{prefix}I could not find a strong catalog match yet. Try asking for a product, "
            "category, budget, or cart goal."
        )

    response_message, used_fallback = synthesize_with_llm(
        user_message=message,
        intent=intent,
        default_message=default_message,
        products=products,
        cart_actions=cart_actions,
        tools_used=tools_used,
    )

    return ChatResponse(
        message=response_message,
        intent=intent,
        products=products,
        cart_actions=cart_actions,
        citations=[
            ChatCitation(product_id=product.id, source_url=product.product_url)
            for product in products
        ],
        follow_up_suggestions=FALLBACK_FOLLOW_UPS,
        tools_used=tools_used,
        fallback=used_fallback,
    )
