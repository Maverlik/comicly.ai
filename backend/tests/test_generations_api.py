from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.v1.generations import get_generation_service
from app.core.errors import ApiError
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.generation import GenerationJob
from app.models.user import User, UserSession
from app.models.wallet import Wallet
from app.services.auth_sessions import hash_session_token
from app.services.blob_storage import StoredBlob
from app.services.comics import ComicCreate, SceneInput, create_comic, replace_scenes
from app.services.generations import GenerationService
from app.services.openrouter import ComicImagePromptInput, OpenRouterImageResult


@pytest.fixture
async def session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


class FakeProvider:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error

    async def generate_image(self, payload: ComicImagePromptInput):
        if self.error is not None:
            raise self.error
        return OpenRouterImageResult(
            image_source="data:image/png;base64,aGVsbG8=",
            model=payload.model_id or "bytedance-seed/seedream-4.5",
            text="base64 should not appear in response",
            prompt="prompt",
            response_payload={"image": "data:image/png;base64,aGVsbG8="},
        )


class FakeStorage:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error

    async def upload_generated_image(self, *, comic_id, page_id, image_source):
        if self.error is not None:
            raise self.error
        return StoredBlob(
            url="https://blob.example/page.png",
            storage_key=f"generated/{page_id}.png",
            content_type="image/png",
            size=5,
        )


@pytest.fixture
async def app_client(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    def override_generation_service() -> GenerationService:
        return GenerationService(
            app.state.settings,
            image_provider=FakeProvider(),
            image_storage=FakeStorage(),
        )

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_generation_service] = override_generation_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def seed_user_and_comic(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    balance: int = 100,
    token: str = "valid-token",
    email: str = "user@example.com",
) -> tuple[User, object, object]:
    async with session_maker() as session:
        user = User(email=email, display_name=email)
        session.add(user)
        await session.flush()
        session.add(Wallet(user_id=user.id, balance=balance))
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        comic = await create_comic(
            session,
            user_id=user.id,
            data=ComicCreate(title="Moon Patrol", story="Story"),
        )
        scenes = await replace_scenes(
            session,
            user_id=user.id,
            comic_id=comic.id,
            scenes=[SceneInput(position=1, title="Launch", description="Launch")],
        )
        await session.commit()
        return user, comic, scenes[0]


def auth_header(token: str = "valid-token") -> dict[str, str]:
    return {"Cookie": f"comicly_session={token}"}


def generation_payload(comic_id, scene_id=None, model_id="bytedance-seed/seedream-4.5"):
    return {
        "comic_id": str(comic_id),
        "scene_id": str(scene_id) if scene_id else None,
        "page_number": 1,
        "story": "A team explores the moon.",
        "characters": "Mira, Sol",
        "style": "Anime",
        "tone": "epic",
        "selectedScene": "Launch",
        "scenes": ["Launch"],
        "dialogue": "Mira: Go!",
        "caption": "Launch day",
        "model_id": model_id,
    }


async def test_generation_requires_authentication(app_client: AsyncClient) -> None:
    response = await app_client.post("/api/v1/generations", json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_generation_requires_idempotency_key(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    _user, comic, scene = await seed_user_and_comic(session_maker)

    response = await app_client.post(
        "/api/v1/generations",
        json=generation_payload(comic.id, scene.id),
        headers=auth_header(),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


async def test_generation_success_returns_small_response_without_base64(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    _user, comic, scene = await seed_user_and_comic(session_maker)

    response = await app_client.post(
        "/api/v1/generations",
        json=generation_payload(comic.id, scene.id),
        headers={**auth_header(), "Idempotency-Key": "api-generate-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["balance"] == 80
    assert payload["image_url"] == "https://blob.example/page.png"
    assert payload["page"]["status"] == "generated"
    assert "base64" not in response.text


async def test_disallowed_model_returns_typed_error(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    _user, comic, scene = await seed_user_and_comic(session_maker)

    response = await app_client.post(
        "/api/v1/generations",
        json=generation_payload(comic.id, scene.id, model_id="blocked/model"),
        headers={**auth_header(), "Idempotency-Key": "blocked-model"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MODEL_NOT_ALLOWED"


async def test_generation_provider_failure_commits_failed_state(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    def override_generation_service() -> GenerationService:
        return GenerationService(
            app.state.settings,
            image_provider=FakeProvider(
                ApiError(502, "OPENROUTER_ERROR", "OpenRouter returned an error.")
            ),
            image_storage=FakeStorage(),
        )

    app.dependency_overrides[get_async_session] = override_session
    app.dependency_overrides[get_generation_service] = override_generation_service
    _user, comic, scene = await seed_user_and_comic(session_maker)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/generations",
            json=generation_payload(comic.id, scene.id),
            headers={**auth_header(), "Idempotency-Key": "provider-fails"},
        )

    async with session_maker() as session:
        job = await session.execute(select(GenerationJob))

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "OPENROUTER_ERROR"
    assert job.scalar_one().status == "failed"
