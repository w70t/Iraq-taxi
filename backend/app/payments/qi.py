"""SuperQi / Qi Card.

Qi's merchant payment API is not publicly documented; integration requires a
commercial agreement with Qi Card, after which they share API specs and
credentials. This provider stays disabled until that lands — the structure
mirrors the other providers so wiring it in later is a single file change.
"""
from .base import PaymentError, PaymentProvider


class QiProvider(PaymentProvider):
    id = "qi"

    @property
    def configured(self) -> bool:
        return False

    async def init(self, trip_id: str, amount: int) -> dict:
        raise PaymentError(
            "SuperQi requires a merchant agreement with Qi Card; "
            "the API specification is provided after onboarding"
        )
