from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.base import Base
from app.models.generation import GenerationJob
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
from app.services.blob_storage import StoredBlob
from app.services.comics import (
    ComicCreate,
    SceneInput,
    create_comic,
    replace_scenes,
)
from app.services.generations import (
    JOB_STATUS_FAILED,
    JOB_STATUS_SUCCEEDED,
    GenerationRequest,
    GenerationService,
)
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


class FakeImageProvider:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.calls: list[ComicImagePromptInput] = []

    async def generate_image(
        self,
        payload: ComicImagePromptInput,
    ) -> OpenRouterImageResult:
        self.calls.append(payload)
        if self.error is not None:
            raise self.error
        return OpenRouterImageResult(
            image_source="data:image/png;base64,aGVsbG8=",
            model=payload.model_id or "bytedance-seed/seedream-4.5",
            text="ok",
            prompt="prompt",
            response_payload={"ok": True},
        )


class FakeImageStorage:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    async def upload_generated_image(self, *, comic_id, page_id, image_source):
        self.calls.append(
            {
                "comic_id": comic_id,
                "page_id": page_id,
                "image_source": image_source,
            }
        )
        if self.error is not None:
            raise self.error
        return StoredBlob(
            url="https://blob.example/page.png",
            storage_key=f"generated/comics/{comic_id}/pages/{page_id}.png",
            content_type="image/png",
            size=5,
        )


async def create_user_wallet_and_comic(
    session_maker: async_sessionmaker[AsyncSession],
    *,
    balance: int = 100,
) -> tuple[User, object, object]:
    async with session_maker() as session:
        user = User(email=f"{uuid4()}@example.com", display_name="User")
        session.add(user)
        await session.flush()
        session.add(Wallet(user_id=user.id, balance=balance))
        comic = await create_comic(
            session,
            user_id=user.id,
            data=ComicCreate(
                title="Moon Patrol",
                story="A team explores the moon.",
                characters="Mira, Sol",
                style="Anime",
                tone="epic",
            ),
        )
        scenes = await replace_scenes(
            session,
            user_id=user.id,
            comic_id=comic.id,
            scenes=[SceneInput(position=1, title="Launch", description="Launch")],
        )
        await session.commit()
        return user, comic, scenes[0]


def generation_request(comic_id, scene_id=None) -> GenerationRequest:
    return GenerationRequest(
        comic_id=comic_id,
        scene_id=scene_id,
        page_number=1,
        story="A team explores the moon.",
        characters="Mira, Sol",
        style="Anime",
        tone="epic",
        selected_scene="Launch",
        scenes=["Launch"],
        dialogue="Mira: Go!",
        caption="Launch day",
        model_id="bytedance-seed/seedream-4.5",
    )


def generation_service(
    *,
    provider: FakeImageProvider | None = None,
    storage: FakeImageStorage | None = None,
) -> GenerationService:
    return GenerationService(
        Settings(_env_file=None, full_page_generation_cost=20),
        image_provider=provider or FakeImageProvider(),
        image_storage=storage or FakeImageStorage(),
    )


async def transaction_amounts(session: AsyncSession) -> list[int]:
    result = await session.execute(
        select(WalletTransaction.amount).order_by(WalletTransaction.amount)
    )
    return list(result.scalars())


async def transaction_count(session: AsyncSession) -> int:
    return (
        await session.scalar(select(func.count()).select_from(WalletTransaction))
    ) or 0


async def test_generation_success_updates_job_page_and_wallet(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, comic, scene = await create_user_wallet_and_comic(session_maker)
    provider = FakeImageProvider()
    storage = FakeImageStorage()
    service = generation_service(provider=provider, storage=storage)

    async with session_maker() as session:
        result = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="generate-1",
        )
        await session.commit()

    assert result.status == JOB_STATUS_SUCCEEDED
    assert result.balance == 80
    assert result.image_url == "https://blob.example/page.png"
    assert result.page.status == "generated"
    assert result.page.model == "bytedance-seed/seedream-4.5"
    assert result.page.coin_cost == 20
    assert result.page.scene_id == scene.id
    assert result.job.status == JOB_STATUS_SUCCEEDED
    assert len(provider.calls) == 1
    assert len(storage.calls) == 1


async def test_same_idempotency_key_replays_without_side_effects(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, comic, scene = await create_user_wallet_and_comic(session_maker)
    provider = FakeImageProvider()
    storage = FakeImageStorage()
    service = generation_service(provider=provider, storage=storage)

    async with session_maker() as session:
        first = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="same-key",
        )
        second = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="same-key",
        )

        assert first.job.id == second.job.id
        assert second.replayed is True
        assert second.balance == 80
        assert len(provider.calls) == 1
        assert len(storage.calls) == 1
        assert await transaction_count(session) == 1


async def test_foreign_user_cannot_reuse_generation_idempotency_key(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    owner, comic, scene = await create_user_wallet_and_comic(session_maker)
    other, other_comic, _other_scene = await create_user_wallet_and_comic(session_maker)
    service = generation_service()

    async with session_maker() as session:
        await service.generate_page(
            session,
            user_id=owner.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="shared-key",
        )

        with pytest.raises(ApiError) as exc_info:
            await service.generate_page(
                session,
                user_id=other.id,
                data=generation_request(other_comic.id),
                idempotency_key="shared-key",
            )

    assert exc_info.value.code == "IDEMPOTENCY_KEY_CONFLICT"


async def test_insufficient_balance_does_not_call_external_services(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, comic, scene = await create_user_wallet_and_comic(session_maker, balance=5)
    provider = FakeImageProvider()
    storage = FakeImageStorage()
    service = generation_service(provider=provider, storage=storage)

    async with session_maker() as session:
        with pytest.raises(ApiError) as exc_info:
            await service.generate_page(
                session,
                user_id=user.id,
                data=generation_request(comic.id, scene.id),
                idempotency_key="too-expensive",
            )

        assert exc_info.value.code == "INSUFFICIENT_COINS"
        assert len(provider.calls) == 0
        assert len(storage.calls) == 0
        assert await transaction_count(session) == 0


async def test_provider_failure_after_debit_marks_failed_and_refunds_once(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, comic, scene = await create_user_wallet_and_comic(session_maker)
    provider = FakeImageProvider(
        ApiError(502, "OPENROUTER_ERROR", "OpenRouter returned an error.")
    )
    storage = FakeImageStorage()
    service = generation_service(provider=provider, storage=storage)

    async with session_maker() as session:
        failed = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="provider-failure",
        )
        replay = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="provider-failure",
        )
        job = (await session.execute(select(GenerationJob))).scalar_one()

        assert failed.status == JOB_STATUS_FAILED
        assert failed.balance == 100
        assert failed.job.error_code == "OPENROUTER_ERROR"
        assert replay.replayed is True
        assert replay.status == JOB_STATUS_FAILED
        assert job.status == JOB_STATUS_FAILED
        assert len(provider.calls) == 1
        assert len(storage.calls) == 0
        assert await transaction_amounts(session) == [-20, 20]


async def test_storage_failure_after_debit_marks_failed_and_refunds_once(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    user, comic, scene = await create_user_wallet_and_comic(session_maker)
    provider = FakeImageProvider()
    storage = FakeImageStorage(
        ApiError(502, "BLOB_STORAGE_ERROR", "Generated image could not be stored.")
    )
    service = generation_service(provider=provider, storage=storage)

    async with session_maker() as session:
        result = await service.generate_page(
            session,
            user_id=user.id,
            data=generation_request(comic.id, scene.id),
            idempotency_key="storage-failure",
        )

        assert result.status == JOB_STATUS_FAILED
        assert result.balance == 100
        assert result.job.error_code == "BLOB_STORAGE_ERROR"
        assert result.page.status == "failed"
        assert len(provider.calls) == 1
        assert len(storage.calls) == 1
        assert await transaction_amounts(session) == [-20, 20]
