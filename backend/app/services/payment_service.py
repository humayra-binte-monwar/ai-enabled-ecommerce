from decimal import Decimal

import httpx
from fastapi import HTTPException, status

from app.core.settings import get_settings
from app.core.supabase_client import get_supabase

SANDBOX_SESSION_URL = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
SANDBOX_VALIDATION_URL = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
LIVE_SESSION_URL = "https://securepay.sslcommerz.com/gwprocess/v4/api.php"
LIVE_VALIDATION_URL = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"


def _payment_urls() -> tuple[str, str]:
    settings = get_settings()
    if settings.sslcommerz_sandbox:
        return SANDBOX_SESSION_URL, SANDBOX_VALIDATION_URL
    return LIVE_SESSION_URL, LIVE_VALIDATION_URL


def start_sslcommerz_payment(order: dict, user_email: str | None) -> str:
    settings = get_settings()
    if not settings.sslcommerz_store_id or not settings.sslcommerz_store_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is not configured.",
        )

    transaction_id = f"ai{order['id'].replace('-', '')[:28]}"
    session_url, _validation_url = _payment_urls()
    callback_base = f"{settings.backend_url.rstrip('/')}/api/payments/sslcommerz"
    payload = {
        "store_id": settings.sslcommerz_store_id,
        "store_passwd": settings.sslcommerz_store_password,
        "total_amount": f"{Decimal(str(order['total'])):.2f}",
        "currency": order["currency"],
        "tran_id": transaction_id,
        "success_url": f"{callback_base}/success",
        "fail_url": f"{callback_base}/fail",
        "cancel_url": f"{callback_base}/cancel",
        "cus_name": order["customer_name"],
        "cus_email": user_email or "customer@example.com",
        "cus_add1": order["customer_address"],
        "cus_city": "Dhaka",
        "cus_country": "Bangladesh",
        "cus_phone": order["customer_phone"],
        "shipping_method": "NO",
        "product_name": "AI Grocery Commerce order",
        "product_category": "Grocery",
        "product_profile": "general",
        "value_a": order["id"],
    }

    try:
        response = httpx.post(session_url, data=payload, timeout=20)
        response.raise_for_status()
        gateway_response = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not start the payment session. Please try again.",
        ) from error

    gateway_url = gateway_response.get("GatewayPageURL")
    if gateway_response.get("status") != "SUCCESS" or not gateway_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The payment gateway could not create a checkout session.",
        )

    get_supabase().table("payments").update(
        {
            "provider": "sslcommerz",
            "provider_payment_id": transaction_id,
            "status": "requires_payment",
        }
    ).eq("order_id", order["id"]).execute()

    return gateway_url


def verify_sslcommerz_payment(callback_data: dict[str, str]) -> str | None:
    validation_id = callback_data.get("val_id")
    if not validation_id:
        return None

    settings = get_settings()
    _session_url, validation_url = _payment_urls()
    try:
        response = httpx.get(
            validation_url,
            params={
                "val_id": validation_id,
                "store_id": settings.sslcommerz_store_id,
                "store_passwd": settings.sslcommerz_store_password,
                "format": "json",
            },
            timeout=20,
        )
        response.raise_for_status()
        validation = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    if validation.get("status") not in {"VALID", "VALIDATED"}:
        return None

    transaction_id = validation.get("tran_id")
    if not transaction_id:
        return None

    supabase = get_supabase()
    payment_response = (
        supabase.table("payments")
        .select("order_id, amount, currency")
        .eq("provider_payment_id", transaction_id)
        .limit(1)
        .execute()
    )
    if not payment_response.data:
        return None

    payment = payment_response.data[0]
    expected_amount = Decimal(str(payment["amount"]))
    received_amount = Decimal(str(validation.get("amount", "-1")))
    if received_amount != expected_amount or validation.get("currency") != payment["currency"]:
        return None

    supabase.table("payments").update(
        {"status": "succeeded", "provider_event_id": validation_id}
    ).eq("order_id", payment["order_id"]).execute()
    supabase.table("orders").update({"status": "paid"}).eq(
        "id", payment["order_id"]
    ).execute()
    return payment["order_id"]


def mark_payment_unsuccessful(transaction_id: str | None, state: str) -> None:
    if not transaction_id:
        return

    supabase = get_supabase()
    payment_response = (
        supabase
        .table("payments")
        .select("order_id")
        .eq("provider_payment_id", transaction_id)
        .execute()
    )
    if not payment_response.data:
        return

    order_id = payment_response.data[0]["order_id"]
    supabase.table("payments").update({"status": state}).eq(
        "provider_payment_id", transaction_id
    ).execute()
    supabase.table("orders").update(
        {"status": "payment_failed" if state == "failed" else "cancelled"}
    ).eq("id", order_id).execute()
