from fastapi import APIRouter

from app.api.v1 import coin_packages

router = APIRouter(prefix="/api/v1")
router.include_router(coin_packages.router)

__all__ = ["router"]
