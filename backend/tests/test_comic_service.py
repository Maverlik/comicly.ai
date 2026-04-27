from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.errors import ApiError
from app.db.base import Base
from app.models.user import User
from app.services.comics import (
    COMIC_STATUS_ARCHIVED,
    ComicCreate,
    ComicUpdate,
    PageInput,
    SceneInput,
    archive_comic,
    create_comic,
    get_comic_detail,
    list_comics,
    replace_pages,
    replace_scenes,
    update_comic,
)


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


async def create_user(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    email: str,
) -> User:
    async with session_maker() as session:
        user = User(email=email, display_name=email)
        session.add(user)
        await session.commit()
        return user


def comic_create(title: str = "Moon Patrol") -> ComicCreate:
    return ComicCreate(
        title=title,
        story="A team explores the moon.",
        characters="Mira, Sol",
        style="Anime",
        tone="Hopeful",
        selected_model="bytedance-seed/seedream-4.5",
    )


async def test_create_update_list_and_archive_comic(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_maker, email="owner@example.com")

    async with session_maker() as session:
        comic = await create_comic(session, user_id=user.id, data=comic_create())
        updated = await update_comic(
            session,
            user_id=user.id,
            comic_id=comic.id,
            data=ComicUpdate(title="Moon Patrol 2", tone="Dramatic"),
        )
        listed_before_archive = await list_comics(session, user_id=user.id)
        archived = await archive_comic(session, user_id=user.id, comic_id=comic.id)
        listed_after_archive = await list_comics(session, user_id=user.id)
        listed_with_archived = await list_comics(
            session,
            user_id=user.id,
            include_archived=True,
        )

    assert comic.title == "Moon Patrol"
    assert comic.story == "A team explores the moon."
    assert comic.style == "Anime"
    assert updated.title == "Moon Patrol 2"
    assert updated.tone == "Dramatic"
    assert [item.id for item in listed_before_archive] == [comic.id]
    assert archived.status == COMIC_STATUS_ARCHIVED
    assert listed_after_archive == []
    assert [item.id for item in listed_with_archived] == [comic.id]


async def test_save_and_reload_structured_scenes_in_order(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_maker, email="owner@example.com")

    async with session_maker() as session:
        comic = await create_comic(session, user_id=user.id, data=comic_create())
        scenes = await replace_scenes(
            session,
            user_id=user.id,
            comic_id=comic.id,
            scenes=[
                SceneInput(
                    position=2,
                    title="Launch",
                    description="The ship leaves.",
                    dialogue="Go!",
                    caption="A bright launch.",
                ),
                SceneInput(
                    position=1,
                    title="Briefing",
                    description="Mission setup.",
                    dialogue="We leave tonight.",
                    caption="The crew gathers.",
                ),
            ],
        )
        detail = await get_comic_detail(session, user_id=user.id, comic_id=comic.id)

    assert [scene.position for scene in scenes] == [1, 2]
    assert [scene.title for scene in detail.scenes] == ["Briefing", "Launch"]
    assert detail.scenes[0].description == "Mission setup."
    assert detail.scenes[0].dialogue == "We leave tonight."
    assert detail.scenes[0].caption == "The crew gathers."


async def test_save_and_reload_page_records_in_order(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_maker, email="owner@example.com")
    generated_at = datetime(2026, 4, 27, tzinfo=UTC)

    async with session_maker() as session:
        comic = await create_comic(session, user_id=user.id, data=comic_create())
        scenes = await replace_scenes(
            session,
            user_id=user.id,
            comic_id=comic.id,
            scenes=[SceneInput(position=1, title="Briefing", description="Setup")],
        )
        pages = await replace_pages(
            session,
            user_id=user.id,
            comic_id=comic.id,
            pages=[
                PageInput(page_number=2, status="pending"),
                PageInput(
                    page_number=1,
                    status="generated",
                    model="model-a",
                    coin_cost=20,
                    image_url="https://example.com/page.png",
                    storage_key="comics/page.png",
                    width=1024,
                    height=1536,
                    scene_id=scenes[0].id,
                    generated_at=generated_at,
                ),
            ],
        )
        detail = await get_comic_detail(session, user_id=user.id, comic_id=comic.id)

    assert [page.page_number for page in pages] == [1, 2]
    assert [page.page_number for page in detail.pages] == [1, 2]
    assert detail.pages[0].status == "generated"
    assert detail.pages[0].model == "model-a"
    assert detail.pages[0].coin_cost == 20
    assert detail.pages[0].image_url == "https://example.com/page.png"
    assert detail.pages[0].storage_key == "comics/page.png"
    assert detail.pages[0].width == 1024
    assert detail.pages[0].height == 1536
    assert detail.pages[0].scene_id == scenes[0].id
    assert detail.pages[0].generated_at == generated_at.replace(tzinfo=None)


async def test_full_detail_restores_draft_metadata_scenes_and_pages(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_maker, email="owner@example.com")

    async with session_maker() as session:
        comic = await create_comic(session, user_id=user.id, data=comic_create())
        await replace_scenes(
            session,
            user_id=user.id,
            comic_id=comic.id,
            scenes=[SceneInput(position=1, title="Scene", description="Story beat")],
        )
        await replace_pages(
            session,
            user_id=user.id,
            comic_id=comic.id,
            pages=[PageInput(page_number=1, status="pending", model="model-a")],
        )
        detail = await get_comic_detail(session, user_id=user.id, comic_id=comic.id)

    assert detail.comic.title == "Moon Patrol"
    assert detail.comic.story == "A team explores the moon."
    assert detail.comic.characters == "Mira, Sol"
    assert detail.comic.style == "Anime"
    assert detail.comic.tone == "Hopeful"
    assert detail.comic.selected_model == "bytedance-seed/seedream-4.5"
    assert len(detail.scenes) == 1
    assert len(detail.pages) == 1


async def test_foreign_user_cannot_access_or_mutate_comic(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    owner = await create_user(session_maker, email="owner@example.com")
    other = await create_user(session_maker, email="other@example.com")

    async with session_maker() as session:
        comic = await create_comic(session, user_id=owner.id, data=comic_create())

        with pytest.raises(ApiError) as detail_error:
            await get_comic_detail(session, user_id=other.id, comic_id=comic.id)
        with pytest.raises(ApiError) as update_error:
            await update_comic(
                session,
                user_id=other.id,
                comic_id=comic.id,
                data=ComicUpdate(title="Stolen"),
            )
        with pytest.raises(ApiError) as scene_error:
            await replace_scenes(
                session,
                user_id=other.id,
                comic_id=comic.id,
                scenes=[SceneInput(position=1, title="Nope", description="Nope")],
            )
        with pytest.raises(ApiError) as page_error:
            await replace_pages(
                session,
                user_id=other.id,
                comic_id=comic.id,
                pages=[PageInput(page_number=1)],
            )
        owner_list = await list_comics(session, user_id=owner.id)
        other_list = await list_comics(session, user_id=other.id)

    assert detail_error.value.code == "COMIC_NOT_FOUND"
    assert update_error.value.code == "COMIC_NOT_FOUND"
    assert scene_error.value.code == "COMIC_NOT_FOUND"
    assert page_error.value.code == "COMIC_NOT_FOUND"
    assert [item.id for item in owner_list] == [comic.id]
    assert other_list == []


async def test_invalid_scene_and_page_inputs_return_stable_errors(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user = await create_user(session_maker, email="owner@example.com")

    async with session_maker() as session:
        comic = await create_comic(session, user_id=user.id, data=comic_create())

        with pytest.raises(ApiError) as duplicate_scene_error:
            await replace_scenes(
                session,
                user_id=user.id,
                comic_id=comic.id,
                scenes=[
                    SceneInput(position=1, title="A", description="A"),
                    SceneInput(position=1, title="B", description="B"),
                ],
            )
        with pytest.raises(ApiError) as negative_cost_error:
            await replace_pages(
                session,
                user_id=user.id,
                comic_id=comic.id,
                pages=[PageInput(page_number=1, coin_cost=-1)],
            )

    assert duplicate_scene_error.value.code == "COMIC_CONFLICT"
    assert negative_cost_error.value.code == "COMIC_VALIDATION_ERROR"
