from fastapi import APIRouter

from api.auth.router import router as auth_router
from api.admin.router import router as admin_router
from api.edge.router import router as edge_router
from api.tunnel.router import router as tunnel_router

router = APIRouter(prefix="/api")

router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(edge_router)
router.include_router(tunnel_router)
