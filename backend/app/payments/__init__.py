from .base import PaymentError, PaymentProvider
from .cash import CashProvider
from .fib import FibProvider
from .qi import QiProvider
from .zaincash import ZainCashProvider

PROVIDERS: dict[str, PaymentProvider] = {
    "cash": CashProvider(),
    "zaincash": ZainCashProvider(),
    "fib": FibProvider(),
    "qi": QiProvider(),
}

__all__ = ["PROVIDERS", "PaymentError", "PaymentProvider"]
