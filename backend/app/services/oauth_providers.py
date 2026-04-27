from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from app.core.config import Settings

SUPPORTED_OAUTH_PROVIDERS = {"google", "yandex"}


class OAuthProviderError(Exception):
    def __init__(self, code: str, message: str = "OAuth provider error.") -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class OAuthProfile:
    provider: str
    provider_user_id: str
    email: str | None
    email_verified: bool
    display_name: str | None
    avatar_url: str | None


def normalize_google_profile(payload: dict) -> OAuthProfile:
    provider_user_id = str(payload.get("sub") or "")
    if not provider_user_id:
        raise OAuthProviderError("OAUTH_PROFILE_MISSING_ID")

    return OAuthProfile(
        provider="google",
        provider_user_id=provider_user_id,
        email=payload.get("email"),
        email_verified=bool(payload.get("email_verified")),
        display_name=payload.get("name"),
        avatar_url=payload.get("picture"),
    )


def normalize_yandex_profile(payload: dict) -> OAuthProfile:
    provider_user_id = str(payload.get("id") or "")
    if not provider_user_id:
        raise OAuthProviderError("OAUTH_PROFILE_MISSING_ID")

    email = payload.get("default_email")
    if email is None and payload.get("emails"):
        email = payload["emails"][0]

    avatar_url = None
    avatar_id = payload.get("default_avatar_id")
    if avatar_id and not payload.get("is_avatar_empty"):
        avatar_url = f"https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200"

    return OAuthProfile(
        provider="yandex",
        provider_user_id=provider_user_id,
        email=email,
        email_verified=bool(
            payload.get("email_verified")
            or payload.get("is_verified")
            or payload.get("verified_email")
        ),
        display_name=payload.get("real_name") or payload.get("display_name"),
        avatar_url=avatar_url,
    )


class OAuthProviderService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def authorize_redirect(
        self,
        *,
        provider: str,
        request: Request,
        redirect_uri: str,
    ):
        client = self._client(provider)
        return await client.authorize_redirect(request, redirect_uri)

    async def authorize_callback(
        self,
        *,
        provider: str,
        request: Request,
    ) -> OAuthProfile:
        client = self._client(provider)
        token = await client.authorize_access_token(request)

        if provider == "google":
            profile_payload = token.get("userinfo")
            if profile_payload is None:
                profile_payload = await client.parse_id_token(request, token)
            return normalize_google_profile(dict(profile_payload))

        response = await client.get(self.settings.yandex_userinfo_endpoint, token=token)
        response.raise_for_status()
        return normalize_yandex_profile(response.json())

    def _client(self, provider: str):
        if provider not in SUPPORTED_OAUTH_PROVIDERS:
            raise OAuthProviderError("OAUTH_PROVIDER_UNSUPPORTED")

        try:
            from authlib.integrations.starlette_client import OAuth
        except ModuleNotFoundError as exc:
            raise OAuthProviderError("OAUTH_DEPENDENCY_MISSING") from exc

        oauth = OAuth()
        if provider == "google":
            if (
                not self.settings.google_client_id
                or not self.settings.google_client_secret
            ):
                raise OAuthProviderError("OAUTH_PROVIDER_NOT_CONFIGURED")
            oauth.register(
                name="google",
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
                server_metadata_url=self.settings.google_server_metadata_url,
                client_kwargs={"scope": "openid email profile"},
            )
            return oauth.google

        if not self.settings.yandex_client_id or not self.settings.yandex_client_secret:
            raise OAuthProviderError("OAUTH_PROVIDER_NOT_CONFIGURED")
        oauth.register(
            name="yandex",
            client_id=self.settings.yandex_client_id,
            client_secret=self.settings.yandex_client_secret,
            authorize_url=self.settings.yandex_authorize_url,
            access_token_url=self.settings.yandex_access_token_url,
            client_kwargs={"scope": "login:email login:info"},
        )
        return oauth.yandex
