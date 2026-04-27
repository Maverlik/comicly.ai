from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import UserSession


@dataclass(frozen=True)
class ProductSessionToken:
    raw_token: str
    token_hash: str
    expires_at: datetime


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def calculate_session_expiry(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.session_lifetime_days)


def build_product_session(settings: Settings) -> ProductSessionToken:
    raw_token = generate_session_token()
    return ProductSessionToken(
        raw_token=raw_token,
        token_hash=hash_session_token(raw_token),
        expires_at=calculate_session_expiry(settings),
    )


async def create_user_session(
    session: AsyncSession,
    *,
    user_id,
    settings: Settings,
) -> ProductSessionToken:
    product_session = build_product_session(settings)
    session.add(
        UserSession(
            user_id=user_id,
            session_token_hash=product_session.token_hash,
            expires_at=product_session.expires_at,
        )
    )
    await session.flush()
    return product_session


def set_product_session_cookie(
    response: Response,
    *,
    token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_lifetime_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        domain=settings.session_cookie_domain,
        path="/",
    )


def clear_product_session_cookie(response: Response, *, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        domain=settings.session_cookie_domain,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )
