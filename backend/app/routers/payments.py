from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Payment, Trip, User
from ..payments import PROVIDERS, PaymentError
from ..payments.fib import FibProvider
from ..payments.zaincash import ZainCashProvider
from ..schemas import PaymentInit
from ..security import current_user, require_role
from ..ws import notify_trip

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/methods")
def methods():
    return [
        {"id": provider.id, "enabled": provider.configured}
        for provider in PROVIDERS.values()
    ]


@router.post("/init")
async def init_payment(
    body: PaymentInit,
    user: User = Depends(require_role("rider")),
    db: Session = Depends(get_db),
):
    trip = db.get(Trip, body.trip_id)
    if trip is None or trip.rider_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    if trip.paid:
        raise HTTPException(status.HTTP_409_CONFLICT, "Trip already paid")

    provider = PROVIDERS[body.method]
    try:
        result = await provider.init(trip.id, trip.fare_estimate)
    except PaymentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    trip.payment_method = body.method
    if body.method != "cash":
        db.add(
            Payment(
                trip_id=trip.id,
                provider=body.method,
                provider_ref=str(result.get("transaction_id") or result.get("payment_id") or ""),
                amount=trip.fare_estimate,
            )
        )
    db.commit()
    return result


@router.get("/zaincash/callback")
async def zaincash_callback(token: str, db: Session = Depends(get_db)):
    provider: ZainCashProvider = PROVIDERS["zaincash"]  # type: ignore[assignment]
    try:
        data = provider.verify_callback(token)
    except PaymentError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    trip = db.get(Trip, data.get("orderid", ""))
    paid = data.get("status") == "success"
    if trip is not None:
        payment = (
            db.query(Payment)
            .filter(Payment.trip_id == trip.id, Payment.provider == "zaincash")
            .order_by(Payment.created_at.desc())
            .first()
        )
        if payment is not None:
            payment.status = "paid" if paid else "failed"
        if paid:
            trip.paid = True
        db.commit()
        await notify_trip(trip, db)

    message = "تم الدفع بنجاح ✅" if paid else "فشل الدفع ❌"
    return HTMLResponse(f"<html><body style='font-family:sans-serif'><h2>{message}</h2>"
                        "<p>يمكنك العودة إلى تطبيق تكسي واحد عراق.</p></body></html>")


@router.post("/fib/check/{payment_id}")
async def fib_check(
    payment_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    payment = (
        db.query(Payment)
        .filter(Payment.provider == "fib", Payment.provider_ref == payment_id)
        .one_or_none()
    )
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")

    provider: FibProvider = PROVIDERS["fib"]  # type: ignore[assignment]
    try:
        fib_status = await provider.check_status(payment_id)
    except PaymentError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    if fib_status == "PAID" and payment.status != "paid":
        payment.status = "paid"
        trip = db.get(Trip, payment.trip_id)
        if trip is not None:
            trip.paid = True
        db.commit()
        if trip is not None:
            await notify_trip(trip, db)
    elif fib_status == "DECLINED":
        payment.status = "failed"
        db.commit()

    return {"status": payment.status, "provider_status": fib_status}
