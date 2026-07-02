"""Fare estimation: base + per-km over straight-line distance.

Straight-line (haversine) underestimates road distance, so PER_KM rates are
tuned upward. Replace with OSRM route distance when a routing server is added.
"""
import math

TARIFFS = {
    #        base   per km   minimum
    "economy": (2_000, 600, 5_000),
    "family": (3_000, 800, 8_000),
    "premium": (4_500, 1_200, 12_000),
}

ROUND_TO = 250


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate(tier: str, pickup_lat: float, pickup_lng: float,
             dest_lat: float | None, dest_lng: float | None) -> int:
    base, per_km, minimum = TARIFFS.get(tier, TARIFFS["economy"])
    if dest_lat is None or dest_lng is None:
        return minimum
    km = haversine_km(pickup_lat, pickup_lng, dest_lat, dest_lng)
    fare = base + per_km * km * 1.3  # 1.3 ≈ road factor over straight line
    fare = max(fare, minimum)
    return int(round(fare / ROUND_TO) * ROUND_TO)
