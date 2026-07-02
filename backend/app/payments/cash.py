from .base import PaymentProvider


class CashProvider(PaymentProvider):
    """Cash on arrival — settled in the car, marked paid on trip completion."""

    id = "cash"

    @property
    def configured(self) -> bool:
        return True

    async def init(self, trip_id: str, amount: int) -> dict:
        return {"method": "cash", "instructions": "ادفع للسائق نقداً عند الوصول"}
