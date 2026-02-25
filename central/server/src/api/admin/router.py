from fastapi import APIRouter

from api.admin.admins import router as admins_router
from api.admin.buildings import router as buildings_router
from api.admin.rooms import router as rooms_router
from api.admin.persons import router as persons_router
from api.admin.hardware import router as hardware_router
from api.admin.sessions import router as sessions_router

router = APIRouter()

# router.include_router(admins_router)
router.include_router(buildings_router)
router.include_router(rooms_router)
router.include_router(persons_router)
router.include_router(hardware_router)
router.include_router(sessions_router)
