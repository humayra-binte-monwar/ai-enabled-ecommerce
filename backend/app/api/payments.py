from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.settings import get_settings
from app.services.payment_service import mark_payment_unsuccessful, verify_sslcommerz_payment

router = APIRouter(prefix="/api/payments", tags=["payments"])


def payment_result_url(result: str, order_id: str | None = None) -> str:
    settings = get_settings()
    url = f"{settings.frontend_url.rstrip('/')}/checkout/result?status={result}"
    return f"{url}&order_id={order_id}" if order_id else url


async def callback_data(request: Request) -> dict[str, str]:
    if request.method == "POST":
        form = await request.form()
        return {key: str(value) for key, value in form.items()}
    return {key: value for key, value in request.query_params.items()}


@router.api_route("/sslcommerz/success", methods=["GET", "POST"])
async def sslcommerz_success(request: Request):
    data = await callback_data(request)
    order_id = verify_sslcommerz_payment(data)
    result = "paid" if order_id else "verification_failed"
    return RedirectResponse(payment_result_url(result, order_id), status_code=303)


@router.api_route("/sslcommerz/fail", methods=["GET", "POST"])
async def sslcommerz_fail(request: Request):
    data = await callback_data(request)
    mark_payment_unsuccessful(data.get("tran_id"), "failed")
    return RedirectResponse(payment_result_url("failed", data.get("value_a")), status_code=303)


@router.api_route("/sslcommerz/cancel", methods=["GET", "POST"])
async def sslcommerz_cancel(request: Request):
    data = await callback_data(request)
    mark_payment_unsuccessful(data.get("tran_id"), "cancelled")
    return RedirectResponse(payment_result_url("cancelled", data.get("value_a")), status_code=303)
