from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.db.session import get_async_session
from app.services.current_user import CurrentUserContext, get_current_user
from app.services.generations import (
    JOB_STATUS_FAILED,
    GenerationRequest,
    GenerationResult,
    GenerationService,
)
from app.services.image_storage import build_image_storage
from app.services.openrouter import OpenRouterService

router = APIRouter(prefix="/generations", tags=["generations"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]
IdempotencyKeyDep = Annotated[str | None, Header(alias="Idempotency-Key")]


class GenerationCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    comic_id: UUID
    scene_id: UUID | None = None
    page_number: int = 1
    story: str
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_scene: str | None = None
    scenes: list[str] | None = None
    dialogue: str | None = None
    caption: str | None = None
    layout: str | None = None
    model_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_creator_aliases(cls, value):
        if isinstance(value, dict):
            normalized = dict(value)
            if "selectedScene" in normalized and "selected_scene" not in normalized:
                normalized["selected_scene"] = normalized["selectedScene"]
            if "model" in normalized and "model_id" not in normalized:
                normalized["model_id"] = normalized["model"]
            return normalized
        return value

    def to_service_input(self) -> GenerationRequest:
        return GenerationRequest(
            comic_id=self.comic_id,
            scene_id=self.scene_id,
            page_number=self.page_number,
            story=self.story,
            characters=self.characters,
            style=self.style,
            tone=self.tone,
            selected_scene=self.selected_scene,
            scenes=self.scenes,
            dialogue=self.dialogue,
            caption=self.caption,
            layout=self.layout,
            model_id=self.model_id,
        )


class GenerationJobResponse(BaseModel):
    id: UUID
    status: str
    model: str | None
    coin_cost: int
    error_code: str | None
    error_message: str | None


class GenerationPageResponse(BaseModel):
    id: UUID
    page_number: int
    status: str
    model: str | None
    coin_cost: int | None
    image_url: str | None
    storage_key: str | None
    width: int | None
    height: int | None
    scene_id: UUID | None
    generated_at: datetime | None


class GenerationCreateResponse(BaseModel):
    job: GenerationJobResponse
    page: GenerationPageResponse
    balance: int
    image_url: str | None
    status: str
    replayed: bool


def get_generation_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenerationService:
    return GenerationService(
        settings,
        image_provider=OpenRouterService(settings),
        image_storage=build_image_storage(settings),
    )


@router.post("", response_model=GenerationCreateResponse)
async def create_generation(
    payload: GenerationCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    idempotency_key: IdempotencyKeyDep = None,
    service: Annotated[GenerationService, Depends(get_generation_service)] = None,
) -> GenerationCreateResponse:
    result = await service.generate_page(
        session,
        user_id=current_user.user.id,
        data=payload.to_service_input(),
        idempotency_key=idempotency_key,
    )
    await session.commit()
    if result.status == JOB_STATUS_FAILED:
        raise ApiError(
            status_code=502,
            code=result.job.error_code or "GENERATION_FAILED",
            message=result.job.error_message or "Generation failed.",
        )
    return _generation_response(result)


def _generation_response(result: GenerationResult) -> GenerationCreateResponse:
    return GenerationCreateResponse(
        job=GenerationJobResponse(
            id=result.job.id,
            status=result.job.status,
            model=result.job.model,
            coin_cost=result.job.coin_cost,
            error_code=result.job.error_code,
            error_message=result.job.error_message,
        ),
        page=GenerationPageResponse(
            id=result.page.id,
            page_number=result.page.page_number,
            status=result.page.status,
            model=result.page.model,
            coin_cost=result.page.coin_cost,
            image_url=result.page.image_url,
            storage_key=result.page.storage_key,
            width=result.page.width,
            height=result.page.height,
            scene_id=result.page.scene_id,
            generated_at=result.page.generated_at,
        ),
        balance=result.balance,
        image_url=result.image_url,
        status=result.status,
        replayed=result.replayed,
    )
