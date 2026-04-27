from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import ProviderIdentity, User, UserProfile
from app.models.wallet import Wallet, WalletTransaction
from app.services.oauth_providers import OAuthProfile


class AuthBootstrapService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def bootstrap_oauth_user(
        self,
        session: AsyncSession,
        *,
        profile: OAuthProfile,
    ) -> User:
        existing_user = await self._find_user_by_provider(session, profile)
        if existing_user is not None:
            return existing_user

        user = await self._find_verified_email_user(session, profile)
        is_new_user = user is None
        if user is None:
            user = User(
                email=profile.email if profile.email_verified else None,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
            )
            session.add(user)
            await session.flush()
        else:
            user.display_name = user.display_name or profile.display_name
            user.avatar_url = user.avatar_url or profile.avatar_url

        session.add(
            ProviderIdentity(
                user_id=user.id,
                provider=profile.provider,
                provider_user_id=profile.provider_user_id,
                provider_email=profile.email,
            )
        )
        await session.flush()

        if is_new_user:
            await self._create_profile_wallet_and_starter_grant(session, user)

        return user

    async def _find_user_by_provider(
        self,
        session: AsyncSession,
        profile: OAuthProfile,
    ) -> User | None:
        result = await session.execute(
            select(User)
            .join(ProviderIdentity, ProviderIdentity.user_id == User.id)
            .where(
                ProviderIdentity.provider == profile.provider,
                ProviderIdentity.provider_user_id == profile.provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _find_verified_email_user(
        self,
        session: AsyncSession,
        profile: OAuthProfile,
    ) -> User | None:
        if not profile.email or not profile.email_verified:
            return None
        result = await session.execute(select(User).where(User.email == profile.email))
        return result.scalar_one_or_none()

    async def _create_profile_wallet_and_starter_grant(
        self,
        session: AsyncSession,
        user: User,
    ) -> None:
        session.add(UserProfile(user_id=user.id))
        wallet = Wallet(user_id=user.id, balance=self.settings.starter_coins)
        session.add(wallet)
        await session.flush()
        session.add(
            WalletTransaction(
                wallet_id=wallet.id,
                user_id=user.id,
                amount=self.settings.starter_coins,
                balance_after=self.settings.starter_coins,
                reason="starter_grant",
                reference_type="auth_bootstrap",
                reference_id=user.id,
                idempotency_key=f"starter-grant:{user.id}",
            )
        )
        await session.flush()
