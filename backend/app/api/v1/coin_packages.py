from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.coin_packages import ensure_default_coin_packages

router = APIRouter(prefix="/coin-packages", tags=["coin-packages"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


class CoinPackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    coin_amount: int
    amount: Decimal
    currency: str
    active: bool


@router.get("", response_model=list[CoinPackageResponse])
async def get_coin_packages(
    session: SessionDep,
) -> list[CoinPackageResponse]:
    packages = await ensure_default_coin_packages(session)
    await session.commit()
    return packages
