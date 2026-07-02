"""OTP delivery.

Production: implement `SmsSender.send` against an SMS gateway that covers
Iraqi operators (AsiaCell / Zain / Korek aggregators), then swap it in via
`get_sender`. Until then the console sender prints codes to the server log.
"""


class SmsSender:
    def send(self, phone: str, code: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleSmsSender(SmsSender):
    """Dev-only sender: prints the OTP instead of sending an SMS."""

    def __init__(self) -> None:
        self.last_codes: dict[str, str] = {}  # used by the test-suite

    def send(self, phone: str, code: str) -> None:
        self.last_codes[phone] = code
        print(f"[OTP] {phone} -> {code}")


_sender = ConsoleSmsSender()


def get_sender() -> SmsSender:
    return _sender
