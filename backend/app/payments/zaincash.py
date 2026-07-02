"""ZainCash merchant API integration.

Live flow (activates once the merchant credentials from your Zain Iraq
contract are set in the environment):

1. Backend builds a JWT signed with the merchant secret and POSTs it to
   `{base}/transaction/init` -> transaction id.
2. The app opens `{base}/transaction/pay?id=...` where the customer confirms
   in their ZainCash wallet.
3. ZainCash redirects to ZAINCASH_REDIRECT_URL with a signed `token` that the
   backend verifies in /payments/zaincash/callback and marks the trip paid.

Test environment: https://test.zaincash.iq (Zain provides test wallets).
"""
import time

import httpx
import jwt

from .. import config
from .base import PaymentError, PaymentProvider


class ZainCashProvider(PaymentProvider):
    id = "zaincash"

    @property
    def configured(self) -> bool:
        return bool(
            config.ZAINCASH_MSISDN
            and config.ZAINCASH_MERCHANT_ID
            and config.ZAINCASH_SECRET
            and config.ZAINCASH_REDIRECT_URL
        )

    async def init(self, trip_id: str, amount: int) -> dict:
        if not self.configured:
            raise PaymentError("ZainCash merchant credentials are not configured")
        if amount < 250:
            raise PaymentError("ZainCash minimum amount is 250 IQD")

        now = int(time.time())
        token = jwt.encode(
            {
                "amount": amount,
                "serviceType": config.ZAINCASH_SERVICE_TYPE,
                "msisdn": config.ZAINCASH_MSISDN,
                "orderId": trip_id,
                "redirectUrl": config.ZAINCASH_REDIRECT_URL,
                "iat": now,
                "exp": now + 60 * 60 * 4,
            },
            config.ZAINCASH_SECRET,
            algorithm="HS256",
        )

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{config.ZAINCASH_BASE_URL}/transaction/init",
                data={
                    "token": token,
                    "merchantId": config.ZAINCASH_MERCHANT_ID,
                    "lang": "ar",
                },
            )
        if response.status_code != 200:
            raise PaymentError(f"ZainCash init failed: HTTP {response.status_code}")
        body = response.json()
        transaction_id = body.get("id")
        if not transaction_id:
            raise PaymentError(f"ZainCash init failed: {body}")

        return {
            "method": "zaincash",
            "transaction_id": transaction_id,
            "pay_url": f"{config.ZAINCASH_BASE_URL}/transaction/pay?id={transaction_id}",
        }

    def verify_callback(self, token: str) -> dict:
        """Decode the signed redirect token; returns {orderid, status, id}."""
        try:
            return jwt.decode(token, config.ZAINCASH_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise PaymentError(f"Invalid ZainCash callback token: {exc}")
