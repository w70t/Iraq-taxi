class PaymentError(Exception):
    """Raised when a provider call fails or the provider is not configured."""


class PaymentProvider:
    """One implementation per payment method.

    `configured` tells the apps whether to offer the method. `init` starts a
    payment and returns provider-specific data the app needs (a redirect URL,
    a QR code, ...). Verification is provider-specific (callback or polling).
    """

    id: str = ""

    @property
    def configured(self) -> bool:  # pragma: no cover - interface
        raise NotImplementedError

    async def init(self, trip_id: str, amount: int) -> dict:  # pragma: no cover
        raise NotImplementedError
