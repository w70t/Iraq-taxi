from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import fares
from ..db import get_db
from ..models import ACTIVE_STATUSES, DriverProfile, Trip, User
from ..schemas import TripCreate
from ..security import current_user, require_role
from ..serializers import trip_dict
from ..ws import notify_trip

router = APIRouter(prefix="/trips", tags=["trips"])


def _active_trip(db: Session, user: User) -> Trip | None:
    column = Trip.rider_id if user.role == "rider" else Trip.driver_id
    return (
        db.query(Trip)
        .filter(column == user.id, Trip.status.in_(ACTIVE_STATUSES))
        .order_by(Trip.created_at.desc())
        .first()
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_trip(
    body: TripCreate,
    user: User = Depends(require_role("rider")),
    db: Session = Depends(get_db),
):
    if _active_trip(db, user) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an active trip")

    trip = Trip(
        rider_id=user.id,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        pickup_label=body.pickup_label,
        dest_lat=body.dest_lat,
        dest_lng=body.dest_lng,
        dest_label=body.dest_label,
        tier=body.tier,
        fare_estimate=fares.estimate(
            body.tier, body.pickup_lat, body.pickup_lng, body.dest_lat, body.dest_lng
        ),
    )
    db.add(trip)
    db.commit()
    return trip_dict(trip, db)


@router.get("/current")
def current_trip(user: User = Depends(current_user), db: Session = Depends(get_db)):
    trip = _active_trip(db, user)
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active trip")
    return trip_dict(trip, db)


@router.get("/history")
def history(user: User = Depends(current_user), db: Session = Depends(get_db)):
    column = Trip.rider_id if user.role == "rider" else Trip.driver_id
    trips = (
        db.query(Trip)
        .filter(column == user.id, Trip.status.in_(["completed", "cancelled"]))
        .order_by(Trip.created_at.desc())
        .limit(50)
        .all()
    )
    return [trip_dict(t, db) for t in trips]


@router.post("/{trip_id}/cancel")
async def cancel_trip(
    trip_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    trip = db.get(Trip, trip_id)
    if trip is None or user.id not in (trip.rider_id, trip.driver_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    if trip.status not in ("requested", "accepted", "arrived"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot cancel a {trip.status} trip")
    trip.status = "cancelled"
    db.commit()
    await notify_trip(trip, db)
    return trip_dict(trip, db)


def _transition(db: Session, trip_id: str, driver: User, from_status: str, to_status: str) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    if trip.status != from_status:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Trip is {trip.status}, expected {from_status}")
    trip.status = to_status
    db.commit()
    return trip


@router.post("/{trip_id}/accept")
async def accept_trip(
    trip_id: str,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    profile = db.get(DriverProfile, driver.id)
    if profile is None or not profile.approved:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Driver account not approved yet")
    if not profile.is_online:
        raise HTTPException(status.HTTP_409_CONFLICT, "Go online before accepting trips")
    if _active_trip(db, driver) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already have an active trip")

    # Atomic claim: only one driver can move requested -> accepted.
    claimed = (
        db.query(Trip)
        .filter(Trip.id == trip_id, Trip.status == "requested")
        .update({"status": "accepted", "driver_id": driver.id})
    )
    if claimed == 0:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Trip already taken or cancelled")
    db.commit()

    trip = db.get(Trip, trip_id)
    await notify_trip(trip, db)
    return trip_dict(trip, db)


@router.post("/{trip_id}/arrived")
async def arrived(
    trip_id: str,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    trip = _transition(db, trip_id, driver, "accepted", "arrived")
    await notify_trip(trip, db)
    return trip_dict(trip, db)


@router.post("/{trip_id}/start")
async def start(
    trip_id: str,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    trip = _transition(db, trip_id, driver, "arrived", "in_progress")
    await notify_trip(trip, db)
    return trip_dict(trip, db)


@router.post("/{trip_id}/complete")
async def complete(
    trip_id: str,
    driver: User = Depends(require_role("driver")),
    db: Session = Depends(get_db),
):
    trip = _transition(db, trip_id, driver, "in_progress", "completed")
    if trip.payment_method == "cash":
        trip.paid = True  # cash is settled in the car
        db.commit()
    await notify_trip(trip, db)
    return trip_dict(trip, db)
