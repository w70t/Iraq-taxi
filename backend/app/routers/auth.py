import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import config
from ..db import get_db
from ..models import DriverProfile, OtpCode, User, now
from ..schemas import OtpRequest, OtpVerify
from ..security import create_token, hash_otp
from ..sms import get_sender

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request")
def request_otp(body: OtpRequest, db: Session = Depends(get_db)):
    entry = (
        db.query(OtpCode)
        .filter(OtpCode.phone == body.phone, OtpCode.role == body.role)
        .one_or_none()
    )

    # Sliding one-hour send window per phone+role to stop SMS abuse.
    if entry and now() - entry.window_start < 3600:
        if entry.sends_in_window >= config.OTP_MAX_SENDS_PER_HOUR:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many OTP requests; try later")
        entry.sends_in_window += 1
    elif entry:
        entry.window_start = now()
        entry.sends_in_window = 1

    code = f"{secrets.randbelow(1_000_000):06d}"
    if entry is None:
        entry = OtpCode(phone=body.phone, role=body.role, code_hash="", expires_at=0)
        db.add(entry)
    entry.code_hash = hash_otp(body.phone, body.role, code)
    entry.expires_at = now() + config.OTP_TTL_SECONDS
    entry.attempts = 0
    db.commit()

    get_sender().send(body.phone, code)

    response: dict = {"sent": True}
    if config.OTP_ECHO:  # DEV ONLY — never enable in production
        response["debug_code"] = code
    return response


@router.post("/otp/verify")
def verify_otp(body: OtpVerify, db: Session = Depends(get_db)):
    entry = (
        db.query(OtpCode)
        .filter(OtpCode.phone == body.phone, OtpCode.role == body.role)
        .one_or_none()
    )
    if entry is None or now() > entry.expires_at:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired; request a new one")
    if entry.attempts >= config.OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts; request a new code")

    entry.attempts += 1
    if hash_otp(body.phone, body.role, body.code) != entry.code_hash:
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Wrong code")

    db.delete(entry)  # single use

    user = (
        db.query(User)
        .filter(User.phone == body.phone, User.role == body.role)
        .one_or_none()
    )
    if user is None:
        user = User(phone=body.phone, role=body.role, name=body.name)
        db.add(user)
        db.flush()
        if body.role == "driver":
            db.add(DriverProfile(user_id=user.id, approved=config.DRIVER_AUTO_APPROVE))
    elif body.name:
        user.name = body.name
    db.commit()

    return {
        "access_token": create_token(user),
        "user": {"id": user.id, "phone": user.phone, "role": user.role, "name": user.name},
    }
