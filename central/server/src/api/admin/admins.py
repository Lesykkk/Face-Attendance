from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.dependencies import AdminDep, DbDep
from core.security import hash_password
from models.admin import Admin
from schemas.admin import AdminCreate, AdminResponse

router = APIRouter(prefix="/admins", tags=["Admins"])


@router.post("", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(body: AdminCreate, db: DbDep, _admin: AdminDep):
    admin = Admin(
        **body.model_dump(exclude={"password"}),
        password_hash=hash_password(body.password)
    )
    db.add(admin)
    try:
        await db.commit()
        await db.refresh(admin)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already exists")
    return AdminResponse(id=admin.id, username=admin.username)
