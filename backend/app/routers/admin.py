"""Admin panel and API: the owner runs the platform from the browser —
fees, tariffs, incentives, revenue stats, payments, complaints and driver
approval. Protected by the X-Admin-Token header (ADMIN_TOKEN env)."""
import hmac
from pathlib import Path

from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..models import Complaint, DriverProfile, Payment, Trip, User, now
from ..routers.complaints import complaint_dict
from ..panel_html import PANEL_HTML
from ..settings_store import SettingsError, get_settings, update_settings

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if not config.ADMIN_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access is disabled: set ADMIN_TOKEN")
    if not hmac.compare_digest(x_admin_token, config.ADMIN_TOKEN):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Wrong admin token")


@router.get("/settings")
def read_settings(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    return get_settings(db)


@router.put("/settings")
def write_settings(
    patch: dict = Body(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return update_settings(db, patch)
    except SettingsError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/stats")
def stats(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    """Owner dashboard: how much the platform earned, and platform health."""
    now_ts = now()
    midnight = now_ts - (now_ts % 86400)

    completed = db.query(Trip).filter(Trip.status == "completed")
    completed_today = completed.filter(Trip.created_at >= midnight)

    by_method: dict = {}
    for trip in completed.all():
        entry = by_method.setdefault(trip.payment_method, {"count": 0, "amount": 0})
        entry["count"] += 1
        entry["amount"] += trip.fare_estimate

    return {
        "revenue_total": sum(t.commission for t in completed.all()),
        "revenue_today": sum(t.commission for t in completed_today.all()),
        "gross_total": sum(t.fare_estimate for t in completed.all()),
        "trips_completed": completed.count(),
        "trips_today": completed_today.count(),
        "trips_active": db.query(Trip).filter(
            Trip.status.in_(["requested", "accepted", "arrived", "in_progress"])
        ).count(),
        "riders": db.query(User).filter(User.role == "rider").count(),
        "drivers": db.query(User).filter(User.role == "driver").count(),
        "drivers_online": db.query(DriverProfile).filter(DriverProfile.is_online.is_(True)).count(),
        "drivers_pending": db.query(DriverProfile).filter(DriverProfile.approved.is_(False)).count(),
        "complaints_open": db.query(Complaint).filter(Complaint.status == "open").count(),
        "payments_by_method": by_method,
    }


@router.get("/complaints")
def list_complaints(
    only_open: bool = True,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if only_open:
        query = query.filter(Complaint.status == "open")
    complaints = query.order_by(Complaint.created_at.desc()).limit(100).all()
    result = []
    for complaint in complaints:
        user = db.get(User, complaint.user_id)
        entry = complaint_dict(complaint)
        entry["user"] = {
            "phone": user.phone if user else "?",
            "name": user.name if user else "",
            "role": user.role if user else "?",
        }
        result.append(entry)
    return result


@router.post("/complaints/{complaint_id}/resolve")
def resolve_complaint(
    complaint_id: str,
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    complaint.status = "resolved"
    complaint.resolved_at = now()
    db.commit()
    return complaint_dict(complaint)


@router.get("/payments")
def list_payments(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(100).all()
    return [
        {
            "id": p.id,
            "trip_id": p.trip_id,
            "provider": p.provider,
            "provider_ref": p.provider_ref,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in payments
    ]


@router.get("/drivers")
def list_drivers(_: None = Depends(require_admin), db: Session = Depends(get_db)):
    drivers = db.query(User).filter(User.role == "driver").order_by(User.created_at.desc()).limit(200).all()
    result = []
    for driver in drivers:
        profile = db.get(DriverProfile, driver.id)
        completed = db.query(Trip).filter(
            Trip.driver_id == driver.id, Trip.status == "completed"
        ).count()
        result.append({
            "id": driver.id,
            "phone": driver.phone,
            "name": driver.name,
            "approved": bool(profile and profile.approved),
            "online": bool(profile and profile.is_online),
            "car_model": profile.car_model if profile else "",
            "plate": profile.plate if profile else "",
            "car_color": profile.car_color if profile else "",
            "photo": profile.photo if profile else "",
            "trips_completed": completed,
        })
    return result


@router.put("/drivers/{driver_id}")
def update_driver(
    driver_id: str,
    body: dict = Body(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Owner edits the driver's public profile: name, car, plate, color, photo."""
    driver = db.get(User, driver_id)
    profile = db.get(DriverProfile, driver_id)
    if driver is None or profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver not found")

    if "name" in body:
        driver.name = str(body["name"]).strip()[:80]
    if "car_model" in body:
        profile.car_model = str(body["car_model"]).strip()[:80]
    if "plate" in body:
        profile.plate = str(body["plate"]).strip()[:30]
    if "car_color" in body:
        color = str(body["car_color"]).strip()
        if color and not (len(color) == 7 and color.startswith("#")):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "car_color must be a #RRGGBB hex value")
        profile.car_color = color
    if "photo" in body:
        photo = str(body["photo"])
        if photo and not photo.startswith("data:image/"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "photo must be a data:image/... URL")
        if len(photo) > 400_000:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "photo too large; resize below ~300KB")
        profile.photo = photo
    db.commit()
    return {"ok": True}


_STATIC = Path(__file__).resolve().parent.parent / "static"


@router.get("/font/{weight}", include_in_schema=False)
def font(weight: str):
    """Self-hosted Cairo font for the panel — works without internet access."""
    name = {"regular": "cairo_regular.ttf", "bold": "cairo_bold.ttf"}.get(weight)
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown font weight")
    return FileResponse(_STATIC / name, media_type="font/ttf")


@router.post("/drivers/{driver_id}/approve")
def approve_driver(
    driver_id: str,
    body: dict = Body(...),
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    profile = db.get(DriverProfile, driver_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Driver not found")
    profile.approved = bool(body.get("approved", True))
    if not profile.approved:
        profile.is_online = False  # suspended drivers go offline immediately
    db.commit()
    return {"approved": profile.approved}


@router.get("", response_class=HTMLResponse, include_in_schema=False)
def panel():
    return HTMLResponse(PANEL_HTML)


