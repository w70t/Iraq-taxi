import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..fares import haversine_km
from ..models import DriverProfile, Trip, User, now
from ..schemas import LocationUpdate, OnlineUpdate
from ..security import require_role
from ..serializers import trip_dict
from ..ws import notify_trip

router = APIRouter(prefix="/drivers", tags=["drivers"])

OPEN_TRIP_RADIUS_KM = 15.0


def _profile(db: Session, driver: User) -> DriverProfile:
    profile = db.get(DriverProfile, driver.id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver profile missing")
    return profile


@router.post("/status")
def set_status(
    body: OnlineUpdate,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    profile = _profile(db, driver)
    if body.online and not profile.approved:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Driver account not approved yet")
    profile.is_online = body.online
    if body.car_model:
        profile.car_model = body.car_model
    if body.plate:
        profile.plate = body.plate
    db.commit()
    return {"online": profile.is_online}


@router.post("/location")
async def update_location(
    body: LocationUpdate,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    from ..models import ACTIVE_STATUSES

    profile = _profile(db, driver)
    profile.last_lat = body.lat
    profile.last_lng = body.lng
    from ..models import now

    profile.location_updated_at = now()
    db.commit()

    # Push the fresh position to the rider of the active trip, if any.
    trip = (
        db.query(Trip)
        .filter(Trip.driver_id == driver.id, Trip.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if trip is not None:
        await notify_trip(trip, db)
    return {"ok": True}


@router.get("/trips/open")
def open_trips(
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    profile = _profile(db, driver)
    trips = (
        db.query(Trip)
        .filter(Trip.status == "requested")
        .order_by(Trip.created_at.desc())
        .limit(30)
        .all()
    )
    if profile.last_lat is not None and profile.last_lng is not None:
        in_range = []
        for trip in trips:
            km = haversine_km(profile.last_lat, profile.last_lng, trip.pickup_lat, trip.pickup_lng)
            if km <= OPEN_TRIP_RADIUS_KM:
                in_range.append((km, trip))
        in_range.sort(key=lambda pair: pair[0])
        return [dict(trip_dict(t, db), distance_km=round(km, 1)) for km, t in in_range]
    return [trip_dict(t, db) for t in trips]


@router.get("/incentives")
def incentives(
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    """Daily bonus ladders plus the driver's completed trips since midnight UTC."""
    now_ts = now()
    midnight = now_ts - (now_ts % 86400)
    trips_today = (
        db.query(Trip)
        .filter(
            Trip.driver_id == driver.id,
            Trip.status == "completed",
            Trip.created_at >= midnight,
        )
        .count()
    )
    plans = json.loads(config.INCENTIVE_PLANS)
    seconds_remaining = 86400 - (now_ts % 86400)
    for plan in plans:
        plan["seconds_remaining"] = seconds_remaining
    return {"trips_today": trips_today, "plans": plans}


@router.get("/earnings")
def earnings(
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    trips = (
        db.query(Trip)
        .filter(Trip.driver_id == driver.id, Trip.status == "completed")
        .order_by(Trip.created_at.desc())
        .all()
    )
    gross = sum(t.fare_estimate for t in trips)
    commission = sum(t.commission for t in trips)
    return {
        "total": gross - commission,  # what the driver actually keeps
        "gross": gross,
        "commission": commission,
        "count": len(trips),
        "trips": [trip_dict(t, db) for t in trips[:50]],
    }
