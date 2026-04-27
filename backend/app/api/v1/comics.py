from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.comics import (
    ComicCreate,
    ComicDetail,
    ComicSummary,
    ComicUpdate,
    PageInput,
    PageSummary,
    SceneInput,
    SceneSummary,
    archive_comic,
    create_comic,
    get_comic_detail,
    list_comics,
    replace_pages,
    replace_scenes,
    update_comic,
)
from app.services.current_user import CurrentUserContext, get_current_user

router = APIRouter(prefix="/comics", tags=["comics"])
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]


class ComicCreateRequest(BaseModel):
    title: str
    story: str | None = None
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_model: str | None = None
    status: str = "draft"


class ComicUpdateRequest(BaseModel):
    title: str | None = None
    story: str | None = None
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_model: str | None = None
    status: str | None = None

    def to_service_input(self) -> ComicUpdate:
        values = {field: getattr(self, field) for field in self.model_fields_set}
        return ComicUpdate(**values)


class SceneRequest(BaseModel):
    position: int
    title: str | None = None
    description: str | None = None
    dialogue: str | None = None
    caption: str | None = None

    def to_service_input(self) -> SceneInput:
        return SceneInput(
            position=self.position,
            title=self.title,
            description=self.description,
            dialogue=self.dialogue,
            caption=self.caption,
        )


class SceneReplaceRequest(BaseModel):
    scenes: list[SceneRequest]


class PageRequest(BaseModel):
    page_number: int
    status: str = "pending"
    model: str | None = None
    coin_cost: int | None = None
    image_url: str | None = None
    storage_key: str | None = None
    width: int | None = None
    height: int | None = None
    scene_id: UUID | None = None
    generated_at: datetime | None = None

    def to_service_input(self) -> PageInput:
        return PageInput(
            page_number=self.page_number,
            status=self.status,
            model=self.model,
            coin_cost=self.coin_cost,
            image_url=self.image_url,
            storage_key=self.storage_key,
            width=self.width,
            height=self.height,
            scene_id=self.scene_id,
            generated_at=self.generated_at,
        )


class PageReplaceRequest(BaseModel):
    pages: list[PageRequest]


class ComicSummaryResponse(BaseModel):
    id: UUID
    title: str
    story: str | None
    characters: str | None
    style: str | None
    tone: str | None
    selected_model: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class SceneResponse(BaseModel):
    id: UUID
    position: int
    title: str | None
    description: str | None
    dialogue: str | None
    caption: str | None
    created_at: datetime
    updated_at: datetime


class PageResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime


class ComicDetailResponse(BaseModel):
    comic: ComicSummaryResponse
    scenes: list[SceneResponse]
    pages: list[PageResponse]


@router.post(
    "",
    response_model=ComicSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_private_comic(
    payload: ComicCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ComicSummaryResponse:
    comic = await create_comic(
        session,
        user_id=current_user.user.id,
        data=ComicCreate(
            title=payload.title,
            story=payload.story,
            characters=payload.characters,
            style=payload.style,
            tone=payload.tone,
            selected_model=payload.selected_model,
            status=payload.status,
        ),
    )
    await session.commit()
    return _comic_response(comic)


@router.get("", response_model=list[ComicSummaryResponse])
async def list_private_comics(
    current_user: CurrentUserDep,
    session: SessionDep,
    include_archived: Annotated[bool, Query()] = False,
) -> list[ComicSummaryResponse]:
    comics = await list_comics(
        session,
        user_id=current_user.user.id,
        include_archived=include_archived,
    )
    return [_comic_response(comic) for comic in comics]


@router.get("/{comic_id}", response_model=ComicDetailResponse)
async def get_private_comic(
    comic_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ComicDetailResponse:
    detail = await get_comic_detail(
        session,
        user_id=current_user.user.id,
        comic_id=comic_id,
    )
    return _detail_response(detail)


@router.patch("/{comic_id}", response_model=ComicSummaryResponse)
async def update_private_comic(
    comic_id: UUID,
    payload: ComicUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ComicSummaryResponse:
    comic = await update_comic(
        session,
        user_id=current_user.user.id,
        comic_id=comic_id,
        data=payload.to_service_input(),
    )
    await session.commit()
    return _comic_response(comic)


@router.delete("/{comic_id}", response_model=ComicSummaryResponse)
async def archive_private_comic(
    comic_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ComicSummaryResponse:
    comic = await archive_comic(
        session,
        user_id=current_user.user.id,
        comic_id=comic_id,
    )
    await session.commit()
    return _comic_response(comic)


@router.put("/{comic_id}/scenes", response_model=list[SceneResponse])
async def replace_private_comic_scenes(
    comic_id: UUID,
    payload: SceneReplaceRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[SceneResponse]:
    scenes = await replace_scenes(
        session,
        user_id=current_user.user.id,
        comic_id=comic_id,
        scenes=[scene.to_service_input() for scene in payload.scenes],
    )
    await session.commit()
    return [_scene_response(scene) for scene in scenes]


@router.put("/{comic_id}/pages", response_model=list[PageResponse])
async def replace_private_comic_pages(
    comic_id: UUID,
    payload: PageReplaceRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[PageResponse]:
    pages = await replace_pages(
        session,
        user_id=current_user.user.id,
        comic_id=comic_id,
        pages=[page.to_service_input() for page in payload.pages],
    )
    await session.commit()
    return [_page_response(page) for page in pages]


def _comic_response(comic: ComicSummary) -> ComicSummaryResponse:
    return ComicSummaryResponse(
        id=comic.id,
        title=comic.title,
        story=comic.story,
        characters=comic.characters,
        style=comic.style,
        tone=comic.tone,
        selected_model=comic.selected_model,
        status=comic.status,
        created_at=comic.created_at,
        updated_at=comic.updated_at,
    )


def _scene_response(scene: SceneSummary) -> SceneResponse:
    return SceneResponse(
        id=scene.id,
        position=scene.position,
        title=scene.title,
        description=scene.description,
        dialogue=scene.dialogue,
        caption=scene.caption,
        created_at=scene.created_at,
        updated_at=scene.updated_at,
    )


def _page_response(page: PageSummary) -> PageResponse:
    return PageResponse(
        id=page.id,
        page_number=page.page_number,
        status=page.status,
        model=page.model,
        coin_cost=page.coin_cost,
        image_url=page.image_url,
        storage_key=page.storage_key,
        width=page.width,
        height=page.height,
        scene_id=page.scene_id,
        generated_at=page.generated_at,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def _detail_response(detail: ComicDetail) -> ComicDetailResponse:
    return ComicDetailResponse(
        comic=_comic_response(detail.comic),
        scenes=[_scene_response(scene) for scene in detail.scenes],
        pages=[_page_response(page) for page in detail.pages],
    )
