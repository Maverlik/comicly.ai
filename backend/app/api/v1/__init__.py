from fastapi import APIRouter

from app.api.v1 import auth, coin_packages, me

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(coin_packages.router)
router.include_router(me.router)

__all__ = ["router"]
