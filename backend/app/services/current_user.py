from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.session import get_async_session
from app.models.user import User, UserSession
from app.services.auth_sessions import hash_session_token


@dataclass(frozen=True)
class CurrentUserContext:
    user: User
    session: UserSession
    token_hash: str


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUserContext:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise ApiError(
            status_code=401,
            code="AUTH_REQUIRED",
            message="Authentication is required.",
        )

    token_hash = hash_session_token(raw_token)
    result = await session.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(UserSession.session_token_hash == token_hash)
    )
    row = result.one_or_none()
    if row is None:
        raise ApiError(
            status_code=401,
            code="SESSION_INVALID",
            message="Session is invalid.",
        )

    user_session, user = row
    if user_session.revoked_at is not None:
        raise ApiError(
            status_code=401,
            code="SESSION_REVOKED",
            message="Session is revoked.",
        )

    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        raise ApiError(
            status_code=401,
            code="SESSION_EXPIRED",
            message="Session is expired.",
        )

    return CurrentUserContext(
        user=user,
        session=user_session,
        token_hash=token_hash,
    )
