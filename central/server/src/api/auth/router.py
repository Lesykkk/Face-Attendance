from fastapi import APIRouter, HTTPException, Response, status
from fastapi.params import Cookie
from typing import Annotated

import jwt
from sqlalchemy import select

from core.dependencies import DbDep
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from core.config import get_settings
from models.admin import Admin
from schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: DbDep):
    result = await db.execute(
        select(Admin).where(Admin.username == body.username)
    )
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    access = create_access_token(str(admin.id))
    refresh = create_refresh_token(str(admin.id))

    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 86400,
        httponly=True,
        samesite="strict",
        secure=False,  # True in production with HTTPS
    )

    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    db: DbDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing refresh token")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
        admin_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    admin = await db.get(Admin, admin_id)
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin not found")

    access = create_access_token(str(admin.id))
    return TokenResponse(access_token=access)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "logged out"}