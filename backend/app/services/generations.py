from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.models.comic import ComicPage
from app.models.generation import GenerationJob
from app.services.comics import (
    PAGE_STATUS_FAILED,
    PAGE_STATUS_GENERATED,
    PageSummary,
    _page_summary,
    prepare_generation_page,
)
from app.services.openrouter import (
    ComicImagePromptInput,
    OpenRouterImageResult,
    build_image_prompt,
    select_image_model,
)
from app.services.wallets import (
    GenerationCostKind,
    debit_generation_cost,
    generation_cost,
    get_wallet_summary,
    refund_generation_debit,
)
from app.services.image_storage_common import StoredImage

JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_TYPE_FULL_PAGE = "full_page"


class ImageProvider(Protocol):
    async def generate_image(
        self,
        payload: ComicImagePromptInput,
    ) -> OpenRouterImageResult: ...


class ImageStorage(Protocol):
    async def upload_generated_image(
        self,
        *,
        comic_id: UUID,
        page_id: UUID,
        image_source: str,
    ) -> StoredImage: ...


@dataclass(frozen=True)
class GenerationRequest:
    comic_id: UUID
    page_number: int
    story: str
    scene_id: UUID | None = None
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_scene: str | None = None
    scenes: list[str] | None = None
    dialogue: str | None = None
    caption: str | None = None
    layout: str | None = None
    model_id: str | None = None


@dataclass(frozen=True)
class GenerationJobSummary:
    id: UUID
    status: str
    model: str | None
    coin_cost: int
    error_code: str | None
    error_message: str | None


@dataclass(frozen=True)
class GenerationResult:
    job: GenerationJobSummary
    page: PageSummary
    balance: int
    image_url: str | None
    status: str
    replayed: bool = False


class GenerationService:
    def __init__(
        self,
        settings: Settings,
        *,
        image_provider: ImageProvider,
        image_storage: ImageStorage,
    ) -> None:
        self._settings = settings
        self._image_provider = image_provider
        self._image_storage = image_storage

    async def generate_page(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        data: GenerationRequest,
        idempotency_key: str | None,
    ) -> GenerationResult:
        key = _require_idempotency_key(idempotency_key)
        existing = await _get_job_by_idempotency_key(session, key=key)
        if existing is not None:
            return await self._replay_existing_job(
                session,
                user_id=user_id,
                job=existing,
            )

        model = select_image_model(self._settings, data.model_id)
        page = await prepare_generation_page(
            session,
            user_id=user_id,
            comic_id=data.comic_id,
            page_number=data.page_number,
            scene_id=data.scene_id,
        )
        prompt_input = _prompt_input(data, model)
        prompt = build_image_prompt(prompt_input)
        cost = generation_cost(self._settings, GenerationCostKind.FULL_PAGE)
        job = GenerationJob(
            user_id=user_id,
            comic_id=data.comic_id,
            scene_id=data.scene_id,
            page_id=page.id,
            status=JOB_STATUS_PROCESSING,
            job_type=JOB_TYPE_FULL_PAGE,
            idempotency_key=key,
            prompt=prompt,
            model=model,
            provider="openrouter",
            coin_cost=cost,
            request_payload=_request_payload(data, model),
            started_at=datetime.now(UTC),
        )
        session.add(job)
        await session.flush()

        debit = await debit_generation_cost(
            session,
            user_id=user_id,
            settings=self._settings,
            kind=GenerationCostKind.FULL_PAGE,
            reference_type="generation_job",
            reference_id=job.id,
            idempotency_key=f"generation-debit:{job.id}",
        )

        try:
            image_result = await self._image_provider.generate_image(prompt_input)
            stored = await self._image_storage.upload_generated_image(
                comic_id=data.comic_id,
                page_id=page.id,
                image_source=image_result.image_source,
            )
        except ApiError as exc:
            return await self._fail_after_debit(
                session,
                user_id=user_id,
                job=job,
                page=page,
                debit_amount=cost,
                debit_reference_id=debit.transaction.id,
                error=exc,
            )

        now = datetime.now(UTC)
        page.status = PAGE_STATUS_GENERATED
        page.model = image_result.model
        page.coin_cost = cost
        page.image_url = stored.url
        page.storage_key = stored.storage_key
        page.generated_at = now
        job.status = JOB_STATUS_SUCCEEDED
        job.model = image_result.model
        job.response_payload = _safe_response_payload(
            image_result.response_payload,
            stored=stored,
        )
        job.completed_at = now
        await session.flush()
        await session.refresh(page)
        return GenerationResult(
            job=_job_summary(job),
            page=_page_summary(page),
            balance=debit.balance,
            image_url=page.image_url,
            status=JOB_STATUS_SUCCEEDED,
        )

    async def _replay_existing_job(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        job: GenerationJob,
    ) -> GenerationResult:
        if job.user_id != user_id:
            raise ApiError(
                status_code=409,
                code="IDEMPOTENCY_KEY_CONFLICT",
                message="Idempotency key belongs to another generation.",
            )
        if job.status not in {JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED}:
            raise ApiError(
                status_code=409,
                code="GENERATION_IN_PROGRESS",
                message="Generation is still in progress.",
            )
        page = await _get_job_page(session, job=job)
        wallet = await get_wallet_summary(session, user_id=user_id, recent_limit=0)
        return GenerationResult(
            job=_job_summary(job),
            page=_page_summary(page),
            balance=wallet.balance,
            image_url=page.image_url,
            status=job.status,
            replayed=True,
        )

    async def _fail_after_debit(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        job: GenerationJob,
        page: ComicPage,
        debit_amount: int,
        debit_reference_id: UUID,
        error: ApiError,
    ) -> GenerationResult:
        refund = await refund_generation_debit(
            session,
            user_id=user_id,
            amount=debit_amount,
            reference_type="generation_job",
            reference_id=debit_reference_id,
            idempotency_key=f"generation-refund:{job.id}",
        )
        now = datetime.now(UTC)
        page.status = PAGE_STATUS_FAILED
        page.coin_cost = debit_amount
        page.model = job.model
        job.status = JOB_STATUS_FAILED
        job.error_code = error.code
        job.error_message = error.message
        job.completed_at = now
        await session.flush()
        await session.refresh(page)
        return GenerationResult(
            job=_job_summary(job),
            page=_page_summary(page),
            balance=refund.balance,
            image_url=None,
            status=JOB_STATUS_FAILED,
        )


async def _get_job_by_idempotency_key(
    session: AsyncSession,
    *,
    key: str,
) -> GenerationJob | None:
    result = await session.execute(
        select(GenerationJob).where(GenerationJob.idempotency_key == key)
    )
    return result.scalar_one_or_none()


async def _get_job_page(session: AsyncSession, *, job: GenerationJob) -> ComicPage:
    if job.page_id is None:
        raise ApiError(
            status_code=409,
            code="GENERATION_RESULT_NOT_READY",
            message="Generation result page is not available.",
        )
    result = await session.execute(select(ComicPage).where(ComicPage.id == job.page_id))
    page = result.scalar_one_or_none()
    if page is None:
        raise ApiError(
            status_code=409,
            code="GENERATION_RESULT_NOT_READY",
            message="Generation result page is not available.",
        )
    return page


def _require_idempotency_key(idempotency_key: str | None) -> str:
    key = (idempotency_key or "").strip()
    if not key:
        raise ApiError(
            status_code=400,
            code="IDEMPOTENCY_KEY_REQUIRED",
            message="Idempotency-Key header is required for billable operations.",
        )
    return key


def _prompt_input(data: GenerationRequest, model: str) -> ComicImagePromptInput:
    return ComicImagePromptInput(
        story=data.story,
        characters=data.characters,
        style=data.style,
        tone=data.tone,
        page=data.page_number,
        selected_scene=data.selected_scene,
        scenes=data.scenes,
        dialogue=data.dialogue,
        caption=data.caption,
        layout=data.layout,
        model_id=model,
    )


def _request_payload(data: GenerationRequest, model: str) -> dict[str, Any]:
    return {
        "comic_id": str(data.comic_id),
        "scene_id": str(data.scene_id) if data.scene_id else None,
        "page_number": data.page_number,
        "story": data.story,
        "characters": data.characters,
        "style": data.style,
        "tone": data.tone,
        "selected_scene": data.selected_scene,
        "scenes": data.scenes,
        "dialogue": data.dialogue,
        "caption": data.caption,
        "layout": data.layout,
        "model_id": model,
    }


def _safe_response_payload(
    response_payload: dict[str, Any],
    *,
    stored: StoredImage,
) -> dict[str, Any]:
    return {
        "openrouter": response_payload,
        "storage": {
            "url": stored.url,
            "storage_key": stored.storage_key,
            "content_type": stored.content_type,
            "size": stored.size,
        },
    }


def _job_summary(job: GenerationJob) -> GenerationJobSummary:
    return GenerationJobSummary(
        id=job.id,
        status=job.status,
        model=job.model,
        coin_cost=job.coin_cost,
        error_code=job.error_code,
        error_message=job.error_message,
    )
