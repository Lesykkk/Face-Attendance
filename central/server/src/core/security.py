from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from core.config import get_settings

pwd_context = PasswordHash.recommended()
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)



def hash_api_key(api_key: str) -> str:
    return pwd_context.hash(api_key)


def verify_api_key(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)



def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(sub: str) -> str:
    return _create_token(
        {"sub": sub, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY_MINUTES),
    )


def create_refresh_token(sub: str) -> str:
    return _create_token(
        {"sub": sub, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
    )


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
