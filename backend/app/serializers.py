from sqlalchemy.orm import Session

from .models import DriverProfile, Trip, User


def trip_dict(trip: Trip, db: Session) -> dict:
    data = {
        "id": trip.id,
        "status": trip.status,
        "pickup": {"lat": trip.pickup_lat, "lng": trip.pickup_lng, "label": trip.pickup_label},
        "destination": {"lat": trip.dest_lat, "lng": trip.dest_lng, "label": trip.dest_label},
        "tier": trip.tier,
        "fare_estimate": trip.fare_estimate,
        "payment_method": trip.payment_method,
        "paid": trip.paid,
        "created_at": trip.created_at,
        "driver": None,
    }
    if trip.driver_id:
        driver = db.get(User, trip.driver_id)
        profile = db.get(DriverProfile, trip.driver_id)
        if driver:
            data["driver"] = {
                "name": driver.name,
                "car_model": profile.car_model if profile else "",
                "plate": profile.plate if profile else "",
                "lat": profile.last_lat if profile else None,
                "lng": profile.last_lng if profile else None,
            }
    return data
