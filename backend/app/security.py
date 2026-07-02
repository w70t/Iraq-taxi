import hashlib
import hmac
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)


def hash_otp(phone: str, role: str, code: str) -> str:
    message = f"{phone}:{role}:{code}".encode()
    return hmac.new(config.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def create_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "role": user.role,
        "exp": int(time.time()) + config.ACCESS_TOKEN_DAYS * 86400,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    payload = decode_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown user")
    return user


def require_role(role: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires {role} account")
        return user

    return dependency
