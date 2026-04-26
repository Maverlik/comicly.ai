from fastapi import APIRouter

from app.db.health import check_database_ready

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    await check_database_ready()
    return {"status": "ready"}
