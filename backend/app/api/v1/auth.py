from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.session import get_async_session
from app.services.auth_bootstrap import AuthBootstrapService
from app.services.auth_sessions import create_user_session, set_product_session_cookie
from app.services.oauth_providers import (
    SUPPORTED_OAUTH_PROVIDERS,
    OAuthProviderError,
    OAuthProviderService,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_oauth_provider_service(
    settings: SettingsDep,
) -> OAuthProviderService:
    return OAuthProviderService(settings)


def get_auth_bootstrap_service(
    settings: SettingsDep,
) -> AuthBootstrapService:
    return AuthBootstrapService(settings)


ProviderDep = Annotated[OAuthProviderService, Depends(get_oauth_provider_service)]
BootstrapDep = Annotated[AuthBootstrapService, Depends(get_auth_bootstrap_service)]


@router.get("/{provider}/login", name="oauth_login")
async def oauth_login(
    provider: str,
    request: Request,
    settings: SettingsDep,
    oauth_service: ProviderDep,
):
    _validate_provider(provider)
    callback_url = request.url_for("oauth_callback", provider=provider)
    redirect_uri = str(callback_url)
    if settings.oauth_callback_base_url:
        redirect_uri = (
            settings.oauth_callback_base_url.rstrip("/") + callback_url.path
        )
    try:
        return await oauth_service.authorize_redirect(
            provider=provider,
            request=request,
            redirect_uri=redirect_uri,
        )
    except OAuthProviderError as exc:
        raise ApiError(
            status_code=400,
            code=exc.code,
            message="OAuth provider is not available.",
        ) from exc


@router.get("/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: str,
    request: Request,
    settings: SettingsDep,
    oauth_service: ProviderDep,
    bootstrap_service: BootstrapDep,
    session: SessionDep,
):
    _validate_provider(provider)
    try:
        profile = await oauth_service.authorize_callback(
            provider=provider,
            request=request,
        )
        user = await bootstrap_service.bootstrap_oauth_user(session, profile=profile)
        product_session = await create_user_session(
            session,
            user_id=user.id,
            settings=settings,
        )
        await session.commit()
    except OAuthProviderError:
        await session.rollback()
        return RedirectResponse(
            f"{settings.frontend_creator_url}?auth_error=oauth_failed",
            status_code=303,
        )

    response = RedirectResponse(settings.frontend_creator_url, status_code=303)
    set_product_session_cookie(
        response,
        token=product_session.raw_token,
        settings=settings,
    )
    return response


def _validate_provider(provider: str) -> None:
    if provider not in SUPPORTED_OAUTH_PROVIDERS:
        raise ApiError(
            status_code=404,
            code="OAUTH_PROVIDER_UNSUPPORTED",
            message="OAuth provider is not supported.",
        )
