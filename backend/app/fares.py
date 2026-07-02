"""Fare estimation: base + per-km over straight-line distance.

Tariffs, booking fee and commission come from the admin-editable settings
(see settings_store / the /admin panel). Straight-line (haversine)
underestimates road distance, so per-km rates apply a 1.3 road factor.
Replace with OSRM route distance when a routing server is added.
"""
import math

ROUND_TO = 250


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate(settings: dict, tier: str, pickup_lat: float, pickup_lng: float,
             dest_lat: float | None, dest_lng: float | None) -> int:
    tariffs = settings["tariffs"]
    tariff = tariffs.get(tier, tariffs["economy"])
    booking_fee = int(settings.get("booking_fee", 0))
    if dest_lat is None or dest_lng is None:
        return tariff["minimum"] + booking_fee
    km = haversine_km(pickup_lat, pickup_lng, dest_lat, dest_lng)
    fare = tariff["base"] + tariff["per_km"] * km * 1.3
    fare = max(fare, tariff["minimum"])
    return int(round(fare / ROUND_TO) * ROUND_TO) + booking_fee


def commission_for(settings: dict, fare: int) -> int:
    """Platform cut for a completed trip: percentage of fare + booking fee."""
    pct = float(settings.get("commission_percent", 0))
    booking_fee = int(settings.get("booking_fee", 0))
    ride_part = max(fare - booking_fee, 0)
    return int(round(ride_part * pct / 100)) + booking_fee
