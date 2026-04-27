from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile
from app.models.wallet import Wallet


async def get_account_summary(session: AsyncSession, user: User) -> dict[str, Any]:
    profile = (
        await session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    ).scalar_one_or_none()
    wallet = (
        await session.execute(select(Wallet).where(Wallet.user_id == user.id))
    ).scalar_one_or_none()

    return {
        "account": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
        },
        "profile": {
            "username": profile.username if profile else None,
            "bio": profile.bio if profile else None,
        },
        "wallet": {
            "balance": wallet.balance if wallet else 0,
        },
    }


async def update_display_name(
    session: AsyncSession,
    *,
    user: User,
    display_name: str,
) -> User:
    user.display_name = display_name
    await session.flush()
    return user
