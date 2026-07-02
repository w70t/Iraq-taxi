"""FIB (First Iraqi Bank) online payments.

Live flow (activates once FIB merchant credentials are set):

1. Backend gets an OAuth token (client_credentials).
2. Backend creates a payment -> FIB returns a QR code + readable code the
   customer pays with the FIB app.
3. Backend polls `/payments/{id}/status` until PAID.

Staging: https://fib.stage.fib.iq — request credentials from FIB's merchant
onboarding (documentation: https://documenter.getpostman.com/view/18377702/UVCB93tc).
"""
import httpx

from .. import config
from .base import PaymentError, PaymentProvider

TOKEN_PATH = "/auth/realms/fib-online-shop/protocol/openid-connect/token"
PAYMENTS_PATH = "/protected/v1/payments"


class FibProvider(PaymentProvider):
    id = "fib"

    @property
    def configured(self) -> bool:
        return bool(config.FIB_CLIENT_ID and config.FIB_CLIENT_SECRET)

    async def _token(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            f"{config.FIB_BASE_URL}{TOKEN_PATH}",
            data={
                "grant_type": "client_credentials",
                "client_id": config.FIB_CLIENT_ID,
                "client_secret": config.FIB_CLIENT_SECRET,
            },
        )
        if response.status_code != 200:
            raise PaymentError(f"FIB auth failed: HTTP {response.status_code}")
        return response.json()["access_token"]

    async def init(self, trip_id: str, amount: int) -> dict:
        if not self.configured:
            raise PaymentError("FIB merchant credentials are not configured")

        async with httpx.AsyncClient(timeout=30) as client:
            token = await self._token(client)
            response = await client.post(
                f"{config.FIB_BASE_URL}{PAYMENTS_PATH}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "monetaryValue": {"amount": str(amount), "currency": "IQD"},
                    "description": f"TaxiOneIraq trip {trip_id}",
                },
            )
        if response.status_code not in (200, 201):
            raise PaymentError(f"FIB payment create failed: HTTP {response.status_code}")
        body = response.json()
        return {
            "method": "fib",
            "payment_id": body.get("paymentId"),
            "qr_code": body.get("qrCode"),
            "readable_code": body.get("readableCode"),
            "valid_until": body.get("validUntil"),
        }

    async def check_status(self, payment_id: str) -> str:
        """Returns FIB status: PAID / UNPAID / DECLINED."""
        if not self.configured:
            raise PaymentError("FIB merchant credentials are not configured")
        async with httpx.AsyncClient(timeout=30) as client:
            token = await self._token(client)
            response = await client.get(
                f"{config.FIB_BASE_URL}{PAYMENTS_PATH}/{payment_id}/status",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            raise PaymentError(f"FIB status check failed: HTTP {response.status_code}")
        return response.json().get("status", "UNPAID")
