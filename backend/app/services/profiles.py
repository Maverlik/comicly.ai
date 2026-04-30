from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserProfile
from app.models.wallet import Wallet


async def get_account_summary(session: AsyncSession, user: User) -> dict[str, Any]:
    result = await session.execute(
        select(User, UserProfile, Wallet)
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .outerjoin(Wallet, Wallet.user_id == User.id)
        .where(User.id == user.id)
    )
    db_user, profile, wallet = result.one()

    return {
        "account": {
            "id": db_user.id,
            "email": db_user.email,
            "display_name": db_user.display_name,
            "avatar_url": db_user.avatar_url,
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
