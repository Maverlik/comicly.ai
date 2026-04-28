from fastapi import APIRouter

from app.api.v1 import ai_text, auth, coin_packages, comics, generations, me, wallet

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(ai_text.router)
router.include_router(coin_packages.router)
router.include_router(comics.router)
router.include_router(generations.router)
router.include_router(me.router)
router.include_router(wallet.router)

__all__ = ["router"]
