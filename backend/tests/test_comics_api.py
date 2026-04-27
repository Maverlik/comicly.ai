from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_app
from app.models.user import User, UserSession
from app.services.auth_sessions import hash_session_token


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


@pytest.fixture
async def app_client(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


async def seed_authenticated_user(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    email: str = "user@example.com",
    token: str = "valid-token",
) -> User:
    async with session_maker() as session:
        user = User(email=email, display_name=email)
        session.add(user)
        await session.flush()
        session.add(
            UserSession(
                user_id=user.id,
                session_token_hash=hash_session_token(token),
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        await session.commit()
        return user


def auth_header(token: str = "valid-token") -> dict[str, str]:
    return {"Cookie": f"comicly_session={token}"}


def comic_payload() -> dict[str, str]:
    return {
        "title": "Moon Patrol",
        "story": "A team explores the moon.",
        "characters": "Mira, Sol",
        "style": "Anime",
        "tone": "Hopeful",
        "selected_model": "bytedance-seed/seedream-4.5",
    }


async def create_comic(app_client: AsyncClient, *, token: str = "valid-token") -> str:
    response = await app_client.post(
        "/api/v1/comics",
        json=comic_payload(),
        headers=auth_header(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_comics_require_authentication(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/v1/comics")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_create_list_update_and_archive_comic(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker)

    comic_id = await create_comic(app_client)

    update_response = await app_client.patch(
        f"/api/v1/comics/{comic_id}",
        json={"title": "Moon Patrol 2", "tone": None},
        headers=auth_header(),
    )
    list_response = await app_client.get("/api/v1/comics", headers=auth_header())
    archive_response = await app_client.delete(
        f"/api/v1/comics/{comic_id}",
        headers=auth_header(),
    )
    hidden_response = await app_client.get("/api/v1/comics", headers=auth_header())
    archived_response = await app_client.get(
        "/api/v1/comics?include_archived=true",
        headers=auth_header(),
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Moon Patrol 2"
    assert update_response.json()["tone"] is None
    assert [item["id"] for item in list_response.json()] == [comic_id]
    assert archive_response.json()["status"] == "archived"
    assert hidden_response.json() == []
    assert [item["id"] for item in archived_response.json()] == [comic_id]


async def test_save_and_reload_comic_detail(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker)
    comic_id = await create_comic(app_client)

    scenes_response = await app_client.put(
        f"/api/v1/comics/{comic_id}/scenes",
        json={
            "scenes": [
                {
                    "position": 2,
                    "title": "Launch",
                    "description": "The ship leaves.",
                    "dialogue": "Go!",
                    "caption": "A bright launch.",
                },
                {
                    "position": 1,
                    "title": "Briefing",
                    "description": "Mission setup.",
                },
            ]
        },
        headers=auth_header(),
    )
    scene_id = scenes_response.json()[0]["id"]

    pages_response = await app_client.put(
        f"/api/v1/comics/{comic_id}/pages",
        json={
            "pages": [
                {"page_number": 2, "status": "pending"},
                {
                    "page_number": 1,
                    "status": "generated",
                    "model": "model-a",
                    "coin_cost": 20,
                    "image_url": "https://example.com/page.png",
                    "storage_key": "comics/page.png",
                    "width": 1024,
                    "height": 1536,
                    "scene_id": scene_id,
                    "generated_at": "2026-04-27T00:00:00Z",
                },
            ]
        },
        headers=auth_header(),
    )
    detail_response = await app_client.get(
        f"/api/v1/comics/{comic_id}",
        headers=auth_header(),
    )

    assert scenes_response.status_code == 200
    assert [scene["position"] for scene in scenes_response.json()] == [1, 2]
    assert pages_response.status_code == 200
    assert [page["page_number"] for page in pages_response.json()] == [1, 2]
    payload = detail_response.json()
    assert payload["comic"]["story"] == "A team explores the moon."
    assert [scene["title"] for scene in payload["scenes"]] == ["Briefing", "Launch"]
    assert payload["pages"][0]["status"] == "generated"
    assert payload["pages"][0]["scene_id"] == scene_id
    assert payload["pages"][0]["coin_cost"] == 20


async def test_user_cannot_access_or_mutate_another_users_comic(
    app_client: AsyncClient,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    await seed_authenticated_user(session_maker, email="owner@example.com")
    await seed_authenticated_user(
        session_maker,
        email="other@example.com",
        token="other-token",
    )
    comic_id = await create_comic(app_client)

    detail_response = await app_client.get(
        f"/api/v1/comics/{comic_id}",
        headers=auth_header("other-token"),
    )
    update_response = await app_client.patch(
        f"/api/v1/comics/{comic_id}",
        json={"title": "Stolen"},
        headers=auth_header("other-token"),
    )
    scenes_response = await app_client.put(
        f"/api/v1/comics/{comic_id}/scenes",
        json={"scenes": [{"position": 1, "title": "Nope", "description": "Nope"}]},
        headers=auth_header("other-token"),
    )
    other_list_response = await app_client.get(
        "/api/v1/comics",
        headers=auth_header("other-token"),
    )

    assert detail_response.status_code == 404
    assert detail_response.json()["error"]["code"] == "COMIC_NOT_FOUND"
    assert update_response.status_code == 404
    assert scenes_response.status_code == 404
    assert other_list_response.json() == []
