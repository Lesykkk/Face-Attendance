from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import decode_token, verify_api_key
from models.admin import Admin
from models.edge_node import EdgeNode



DbDep = Annotated[AsyncSession, Depends(get_db)]

async def get_current_admin(
    db: DbDep,
    authorization: Annotated[str | None, Header()] = None,
) -> Admin:
    if authorization is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    token = authorization.removeprefix("Bearer ").strip()
    if not token or token == authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authorization header")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
        admin_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    admin = await db.get(Admin, admin_id)
    if admin is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin not found")
    return admin


AdminDep = Annotated[Admin, Depends(get_current_admin)]


async def get_current_edge_node(
    db: DbDep,
    authorization: Annotated[str | None, Header()] = None,
) -> EdgeNode:
    if authorization is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")

    api_key = authorization.removeprefix("Bearer ").strip()
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")

    result = await db.execute(select(EdgeNode))
    nodes = result.scalars().all()

    for node in nodes:
        if verify_api_key(api_key, node.api_key_hash):
            return node

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")


EdgeNodeDep = Annotated[EdgeNode, Depends(get_current_edge_node)]
