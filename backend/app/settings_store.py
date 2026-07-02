"""Runtime fee settings, editable from the /admin panel without redeploying.

The admin controls the platform's cut here: commission percentage, a fixed
booking fee, and the per-tier tariffs used for fare estimates.
"""
import json

from sqlalchemy.orm import Session

from . import config
from .models import Setting

SETTINGS_KEY = "app"

DEFAULTS: dict = {
    # Platform commission taken from each fare (percent, 0-50).
    "commission_percent": 10.0,
    # Fixed booking fee in IQD added to every fare; goes to the platform.
    "booking_fee": 0,
    # Fare tariffs per tier: base + per_km over road distance, floor at minimum.
    "tariffs": {
        "economy": {"base": 2000, "per_km": 600, "minimum": 5000},
        "family": {"base": 3000, "per_km": 800, "minimum": 8000},
        "premium": {"base": 4500, "per_km": 1200, "minimum": 12000},
    },
    # Driver bonus ladders, editable from /admin (env INCENTIVE_PLANS is the seed).
    "incentive_plans": json.loads(config.INCENTIVE_PLANS),
}


def get_settings(db: Session) -> dict:
    row = db.get(Setting, SETTINGS_KEY)
    stored = {}
    if row is not None:
        try:
            stored = json.loads(row.value)
        except ValueError:
            stored = {}
    merged = json.loads(json.dumps(DEFAULTS))  # deep copy
    merged.update({k: v for k, v in stored.items() if k in DEFAULTS})
    return merged


class SettingsError(ValueError):
    pass


def validate(patch: dict) -> dict:
    clean: dict = {}
    if "commission_percent" in patch:
        pct = float(patch["commission_percent"])
        if not 0 <= pct <= 50:
            raise SettingsError("commission_percent must be between 0 and 50")
        clean["commission_percent"] = pct
    if "booking_fee" in patch:
        fee = int(patch["booking_fee"])
        if not 0 <= fee <= 10_000:
            raise SettingsError("booking_fee must be between 0 and 10000 IQD")
        clean["booking_fee"] = fee
    if "tariffs" in patch:
        tariffs = {}
        for tier in ("economy", "family", "premium"):
            entry = patch["tariffs"].get(tier)
            if entry is None:
                raise SettingsError(f"tariffs.{tier} is required")
            tariffs[tier] = {
                field: _positive(entry, field, tier)
                for field in ("base", "per_km", "minimum")
            }
        clean["tariffs"] = tariffs
    if "incentive_plans" in patch:
        clean["incentive_plans"] = _validate_plans(patch["incentive_plans"])
    return clean


def _validate_plans(plans) -> list:
    if not isinstance(plans, list) or len(plans) > 10:
        raise SettingsError("incentive_plans must be a list of at most 10 plans")
    clean = []
    for index, plan in enumerate(plans):
        title = str(plan.get("title", "")).strip()
        if not title:
            raise SettingsError(f"plan {index + 1}: title is required")
        steps = plan.get("steps")
        if not isinstance(steps, list) or not steps or len(steps) > 10:
            raise SettingsError(f"plan {index + 1}: steps must be a non-empty list (max 10)")
        clean_steps = []
        for step in steps:
            trips = int(step.get("trips", 0))
            bonus = int(step.get("bonus", -1))
            if not 1 <= trips <= 100 or not 0 <= bonus <= 1_000_000:
                raise SettingsError(f"plan {index + 1}: each step needs trips 1-100 and bonus 0-1,000,000")
            clean_steps.append({"trips": trips, "bonus": bonus})
        clean_steps.sort(key=lambda s: s["trips"])
        clean.append({
            "id": str(plan.get("id") or f"plan-{index + 1}"),
            "title": title,
            "description": str(plan.get("description", "")).strip(),
            "steps": clean_steps,
        })
    return clean


def _positive(entry: dict, field: str, tier: str) -> int:
    value = int(entry.get(field, -1))
    if not 0 <= value <= 1_000_000:
        raise SettingsError(f"tariffs.{tier}.{field} must be between 0 and 1,000,000")
    return value


def update_settings(db: Session, patch: dict) -> dict:
    clean = validate(patch)
    current = get_settings(db)
    current.update(clean)
    row = db.get(Setting, SETTINGS_KEY)
    if row is None:
        row = Setting(key=SETTINGS_KEY)
        db.add(row)
    row.value = json.dumps(current)
    db.commit()
    return current
