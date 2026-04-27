from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_async_session
from app.services.auth_sessions import clear_product_session_cookie
from app.services.current_user import CurrentUserContext, get_current_user
from app.services.profiles import get_account_summary, update_display_name

router = APIRouter(prefix="/me", tags=["me"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]


class AccountResponse(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None


class ProfileResponse(BaseModel):
    username: str | None
    bio: str | None


class WalletResponse(BaseModel):
    balance: int


class MeResponse(BaseModel):
    account: AccountResponse
    profile: ProfileResponse
    wallet: WalletResponse


class DisplayNameUpdateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)


@router.get("", response_model=MeResponse)
async def get_me(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> dict:
    return await get_account_summary(session, current_user.user)


@router.patch("", response_model=MeResponse)
async def update_me(
    payload: DisplayNameUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> dict:
    await update_display_name(
        session,
        user=current_user.user,
        display_name=payload.display_name,
    )
    await session.commit()
    return await get_account_summary(session, current_user.user)


@router.post("/logout")
async def logout(
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
) -> JSONResponse:
    current_user.session.revoked_at = datetime.now(UTC)
    await session.commit()
    response = JSONResponse({"ok": True})
    clear_product_session_cookie(response, settings=settings)
    return response
