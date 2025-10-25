from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import Settings, get_settings


class UserRole(str, Enum):
    admin = "admin"
    recruiter = "recruiter"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


class TokenError(Exception):
    """Raised when a JWT token cannot be decoded."""


def create_access_token(
    subject: str,
    role: UserRole,
    settings: Optional[Settings] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    config = settings or get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(seconds=config.jwt_access_token_expires)
    )
    payload = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_access_token(token: str, settings: Optional[Settings] = None) -> dict[str, Any]:
    config = settings or get_settings()
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - jose already well tested
        raise TokenError("Invalid authentication token") from exc
    return payload
