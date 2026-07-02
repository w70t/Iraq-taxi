"""Environment-driven settings. Copy .env.example to .env for local overrides."""
import os
import secrets


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes"}


# --- Core ---------------------------------------------------------------
# In production SECRET_KEY MUST be set; the random fallback invalidates all
# tokens on every restart, which is safe but inconvenient for dev.
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taxi.db")
ACCESS_TOKEN_DAYS = int(os.getenv("ACCESS_TOKEN_DAYS", "7"))

# --- Admin ----------------------------------------------------------------
# Token for the /admin panel and admin API (fees, tariffs). Leave empty to
# disable admin access entirely. Generate one with:
#   python -c "import secrets;print(secrets.token_urlsafe(24))"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# --- OTP ----------------------------------------------------------------
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "300"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_MAX_SENDS_PER_HOUR = int(os.getenv("OTP_MAX_SENDS_PER_HOUR", "5"))
# DEV ONLY: echo the OTP code in the API response so the mobile apps can be
# tested without an SMS contract. MUST be false in production.
OTP_ECHO = _bool("OTP_ECHO", False)

# --- Drivers ------------------------------------------------------------
# In production set to false and approve drivers from the admin side after
# verifying their licence and vehicle documents.
DRIVER_AUTO_APPROVE = _bool("DRIVER_AUTO_APPROVE", True)

# --- Driver incentives ----------------------------------------------------
# Daily bonus ladders shown in the driver app. Override with your own plans
# via the INCENTIVE_PLANS env var (same JSON shape). Bonuses are in IQD and
# reset at midnight UTC.
DEFAULT_INCENTIVE_PLANS = """[
  {
    "id": "daily-ladder",
    "title": "مكافأة الرحلات اليومية",
    "description": "أكمل رحلات اليوم واكسب مكافآت متصاعدة تُضاف إلى أرباحك.",
    "steps": [
      {"trips": 1, "bonus": 2000},
      {"trips": 3, "bonus": 5000},
      {"trips": 6, "bonus": 12000}
    ]
  }
]"""
INCENTIVE_PLANS = os.getenv("INCENTIVE_PLANS", DEFAULT_INCENTIVE_PLANS)

# --- ZainCash merchant credentials (from your Zain Iraq merchant contract) ---
ZAINCASH_BASE_URL = os.getenv("ZAINCASH_BASE_URL", "https://test.zaincash.iq")
ZAINCASH_MSISDN = os.getenv("ZAINCASH_MSISDN", "")          # merchant wallet number
ZAINCASH_MERCHANT_ID = os.getenv("ZAINCASH_MERCHANT_ID", "")
ZAINCASH_SECRET = os.getenv("ZAINCASH_SECRET", "")
ZAINCASH_SERVICE_TYPE = os.getenv("ZAINCASH_SERVICE_TYPE", "TaxiOneIraq ride")
ZAINCASH_REDIRECT_URL = os.getenv("ZAINCASH_REDIRECT_URL", "")

# --- FIB (First Iraqi Bank) merchant credentials -------------------------
FIB_BASE_URL = os.getenv("FIB_BASE_URL", "https://fib.stage.fib.iq")
FIB_CLIENT_ID = os.getenv("FIB_CLIENT_ID", "")
FIB_CLIENT_SECRET = os.getenv("FIB_CLIENT_SECRET", "")
