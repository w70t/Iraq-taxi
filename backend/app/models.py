import time
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def now() -> int:
    return int(time.time())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("phone", "role"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    phone: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)  # rider | driver
    name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    car_model: Mapped[str] = mapped_column(String, default="")
    plate: Mapped[str] = mapped_column(String, default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    __table_args__ = (UniqueConstraint("phone", "role"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    phone: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    code_hash: Mapped[str] = mapped_column(String)
    expires_at: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[int] = mapped_column(Integer, default=now)
    sends_in_window: Mapped[int] = mapped_column(Integer, default=1)


TRIP_STATUSES = ["requested", "accepted", "arrived", "in_progress", "completed", "cancelled"]
ACTIVE_STATUSES = ["requested", "accepted", "arrived", "in_progress"]


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    rider_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    driver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="requested", index=True)

    pickup_lat: Mapped[float] = mapped_column(Float)
    pickup_lng: Mapped[float] = mapped_column(Float)
    pickup_label: Mapped[str] = mapped_column(String, default="")
    dest_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dest_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    dest_label: Mapped[str] = mapped_column(String, default="")

    tier: Mapped[str] = mapped_column(String, default="economy")
    fare_estimate: Mapped[int] = mapped_column(Integer, default=0)
    payment_method: Mapped[str] = mapped_column(String, default="cash")
    paid: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[int] = mapped_column(Integer, default=now)
    updated_at: Mapped[int] = mapped_column(Integer, default=now, onupdate=now)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id"), index=True)
    provider: Mapped[str] = mapped_column(String)  # cash | zaincash | fib | qi
    provider_ref: Mapped[str] = mapped_column(String, default="")
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | paid | failed
    created_at: Mapped[int] = mapped_column(Integer, default=now)
