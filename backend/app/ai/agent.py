import re
import json

from app.ai.guardrails import health_disclaimer, is_health_question
from app.ai.prompts import CHAT_SYNTHESIS_PROMPT, FALLBACK_FOLLOW_UPS, SYSTEM_PROMPT
from app.ai.tools import (
    compare_prices_tool,
    make_add_action,
    make_quantity_action,
    make_remove_action,
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


def looks_like_cart_remove(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["remove", "delete", "drop"]) and "cart" in message_lower


def looks_like_cart_increase(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["increase", "more", "add one", "add 1"]) and (
        "quantity" in message_lower or "cart" in message_lower
    )


def looks_like_cart_decrease(message: str) -> bool:
    message_lower = message.lower()
    return any(term in message_lower for term in ["decrease", "less", "reduce"]) and (
        "quantity" in message_lower or "cart" in message_lower
    )


def looks_like_bundle_request(message: str) -> bool:
    message_lower = message.lower()
    return any(
        term in message_lower
        for term in ["bundle", "basket", "grocery list", "meal plan", "recipe"]
    )


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
        "remove",
        "delete",
        "drop",
        "increase",
        "decrease",
        "reduce",
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


def extract_duration_days(message: str) -> int:
    message_lower = message.lower()
    week_match = re.search(r"(\d+)\s*(?:week|weeks)", message_lower)
    if week_match:
        return max(1, int(week_match.group(1)) * 7)

    day_match = re.search(r"(\d+)\s*(?:day|days)", message_lower)
    if day_match:
        return max(1, int(day_match.group(1)))

    return 7


def find_cart_item(message: str, cart_items) -> object | None:
    query = clean_search_query(message)
    terms = [term for term in query.split() if len(term) > 1]

    if not terms and len(cart_items) == 1:
        return cart_items[0]

    best_match = None
    best_score = 0

    for item in cart_items:
        item_text = f"{item.name} {item.category}".lower()
        score = sum(1 for term in terms if term in item_text)
        if score > best_score:
            best_match = item
            best_score = score

    return best_match


def unique_products(products: list[ChatProductCard]) -> list[ChatProductCard]:
    seen_ids = set()
    unique = []

    for product in products:
        if product.id in seen_ids:
            continue

        unique.append(product)
        seen_ids.add(product.id)

    return unique


def build_multi_meal_grocery_list(message: str) -> tuple[str, list[ChatProductCard]]:
    duration_days = extract_duration_days(message)
    requested_meals = [
        meal
        for meal in ["breakfast", "lunch", "dinner"]
        if meal in message.lower()
    ] or ["breakfast", "lunch", "dinner"]
    products_by_id = {}
    meals_by_product_id = {}
    grouped_names = {}

    for meal in requested_meals:
        bundle = plan_bundle_tool(
            budget=50000,
            people=2,
            duration_days=duration_days,
            meal_type=meal,
        )
        grouped_names[meal] = []

        for item in bundle["items"]:
            grouped_names[meal].append(item.name)

            if item.id not in products_by_id:
                products_by_id[item.id] = ChatProductCard(
                    id=item.id,
                    name=item.name,
                    category=item.category,
                    price=item.price,
                    unit=item.unit,
                    image_url=item.image_url,
                    product_url=item.product_url,
                    reason=f"{meal.title()} plan: {item.reason}",
                )
                meals_by_product_id[item.id] = []

            meals_by_product_id[item.id].append(meal)

    products = []
    for product_id, product in products_by_id.items():
        meal_labels = sorted(set(meals_by_product_id[product_id]))
        product.reason = f"Suggested for {', '.join(meal_labels)}."
        products.append(product)

    meal_sections = []
    for meal in requested_meals:
        names = grouped_names.get(meal, [])
        if names:
            meal_sections.append(
                f"{meal.title()}: " + ", ".join(dict.fromkeys(names))
            )

    return (
        f"Built a {duration_days}-day grocery list for {', '.join(requested_meals)}. "
        + " ".join(meal_sections),
        products[:12],
    )


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
            "normalized_category": product.normalized_category,
            "product_type": product.product_type,
            "tags": product.tags,
            "price": product.price,
            "unit": product.unit,
            "reason": product.reason,
        }
        for product in products[:12]
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
        "cart_actions_count": len(cart_actions),
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


def sanitize_cart_language(message: str, cart_actions: list[ChatCartAction]) -> str:
    if cart_actions:
        return message

    blocked_patterns = [
        r"\s*The app updated the cart\.?",
        r"\s*You should confirm the action\.?",
        r"\s*You should confirm these actions\.?",
        r"\s*Please confirm this action\.?",
        r"\s*Please confirm these actions to proceed\.?",
        r"\s*To add these items to your cart, please confirm[^.]*\.?",
    ]
    cleaned = message

    for pattern in blocked_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def run_chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    query = clean_search_query(message)
    tools_used = []
    products = []
    cart_actions = []
    intent = "product_search"

    if looks_like_cart_remove(message):
        intent = "cart_remove"
        tools_used.append("remove_from_cart")
        item = find_cart_item(message, request.cart_items)
        if item:
            cart_actions.append(make_remove_action(item))
            default_message = cart_actions[0].message
        else:
            default_message = "I could not find that item in your cart."

        response_message, used_fallback = synthesize_with_llm(
            user_message=message,
            intent=intent,
            default_message=default_message,
            products=products,
            cart_actions=cart_actions,
            tools_used=tools_used,
        )
        response_message = sanitize_cart_language(response_message, cart_actions)
        return ChatResponse(
            message=response_message,
            intent=intent,
            cart_actions=cart_actions,
            follow_up_suggestions=FALLBACK_FOLLOW_UPS,
            tools_used=tools_used,
            fallback=used_fallback,
        )

    if looks_like_cart_increase(message) or looks_like_cart_decrease(message):
        intent = "cart_quantity"
        action_type = (
            "increase_quantity"
            if looks_like_cart_increase(message)
            else "decrease_quantity"
        )
        tools_used.append(action_type)
        item = find_cart_item(message, request.cart_items)
        if item:
            cart_actions.append(
                make_quantity_action(action_type, item, extract_quantity(message))
            )
            default_message = cart_actions[0].message
        else:
            default_message = "I could not find that item in your cart."

        response_message, used_fallback = synthesize_with_llm(
            user_message=message,
            intent=intent,
            default_message=default_message,
            products=products,
            cart_actions=cart_actions,
            tools_used=tools_used,
        )
        response_message = sanitize_cart_language(response_message, cart_actions)
        return ChatResponse(
            message=response_message,
            intent=intent,
            cart_actions=cart_actions,
            follow_up_suggestions=FALLBACK_FOLLOW_UPS,
            tools_used=tools_used,
            fallback=used_fallback,
        )

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
        response_message = sanitize_cart_language(response_message, cart_actions)

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
        tools_used.append("plan_bundle")

        if "grocery list" in message.lower() and (
            "breakfast" in message.lower()
            or "lunch" in message.lower()
            or "dinner" in message.lower()
        ):
            default_message, products = build_multi_meal_grocery_list(message)
        else:
            budget = extract_budget(message) or 1500
            bundle = plan_bundle_tool(
                budget=budget,
                people=2,
                duration_days=extract_duration_days(message),
                meal_type=query,
            )
            for bundle_item in bundle["items"][:8]:
                products.append(
                    ChatProductCard(
                        id=bundle_item.id,
                        name=bundle_item.name,
                        category=bundle_item.category,
                        price=bundle_item.price,
                        unit=bundle_item.unit,
                        image_url=bundle_item.image_url,
                        product_url=bundle_item.product_url,
                        reason=bundle_item.reason,
                    )
                )

            default_message = f"{bundle['summary']} Estimated total: Tk {bundle['estimated_total']}."
        response_message, used_fallback = synthesize_with_llm(
            user_message=message,
            intent=intent,
            default_message=default_message,
            products=products,
            cart_actions=cart_actions,
            tools_used=tools_used,
        )
        response_message = sanitize_cart_language(response_message, cart_actions)

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
        tools_used.append("add_to_cart")
        cart_actions.append(make_add_action(products[0], extract_quantity(message)))

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
    response_message = sanitize_cart_language(response_message, cart_actions)

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
