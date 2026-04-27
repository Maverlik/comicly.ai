from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, desc, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.comic import Comic, ComicPage, ComicScene

COMIC_STATUS_DRAFT = "draft"
COMIC_STATUS_GENERATED = "generated"
COMIC_STATUS_FAILED = "failed"
COMIC_STATUS_ARCHIVED = "archived"
COMIC_STATUSES = {
    COMIC_STATUS_DRAFT,
    COMIC_STATUS_GENERATED,
    COMIC_STATUS_FAILED,
    COMIC_STATUS_ARCHIVED,
}

PAGE_STATUS_PENDING = "pending"
PAGE_STATUS_GENERATED = "generated"
PAGE_STATUS_FAILED = "failed"
PAGE_STATUSES = {PAGE_STATUS_PENDING, PAGE_STATUS_GENERATED, PAGE_STATUS_FAILED}


@dataclass(frozen=True)
class ComicCreate:
    title: str
    story: str | None = None
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_model: str | None = None
    status: str = COMIC_STATUS_DRAFT


@dataclass(frozen=True)
class ComicUpdate:
    title: str | None = None
    story: str | None = None
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    selected_model: str | None = None
    status: str | None = None


@dataclass(frozen=True)
class SceneInput:
    position: int
    title: str | None = None
    description: str | None = None
    dialogue: str | None = None
    caption: str | None = None


@dataclass(frozen=True)
class PageInput:
    page_number: int
    status: str = PAGE_STATUS_PENDING
    model: str | None = None
    coin_cost: int | None = None
    image_url: str | None = None
    storage_key: str | None = None
    width: int | None = None
    height: int | None = None
    scene_id: UUID | None = None
    generated_at: datetime | None = None


@dataclass(frozen=True)
class ComicSummary:
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


@dataclass(frozen=True)
class SceneSummary:
    id: UUID
    position: int
    title: str | None
    description: str | None
    dialogue: str | None
    caption: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PageSummary:
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


@dataclass(frozen=True)
class ComicDetail:
    comic: ComicSummary
    scenes: list[SceneSummary]
    pages: list[PageSummary]


async def create_comic(
    session: AsyncSession,
    *,
    user_id: UUID,
    data: ComicCreate,
) -> ComicSummary:
    _validate_status(data.status, allowed=COMIC_STATUSES, field_name="status")
    comic = Comic(
        user_id=user_id,
        title=_required_text(data.title, field_name="title"),
        story=_optional_text(data.story),
        characters=_optional_text(data.characters),
        style=_optional_text(data.style),
        style_preset=_optional_text(data.style),
        tone=_optional_text(data.tone),
        selected_model=_optional_text(data.selected_model),
        status=data.status,
    )
    session.add(comic)
    await session.flush()
    await session.refresh(comic)
    return _comic_summary(comic)


async def update_comic(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
    data: ComicUpdate,
) -> ComicSummary:
    comic = await get_owned_comic(session, user_id=user_id, comic_id=comic_id)

    if data.title is not None:
        comic.title = _required_text(data.title, field_name="title")
    if data.story is not None:
        comic.story = _optional_text(data.story)
    if data.characters is not None:
        comic.characters = _optional_text(data.characters)
    if data.style is not None:
        comic.style = _optional_text(data.style)
        comic.style_preset = _optional_text(data.style)
    if data.tone is not None:
        comic.tone = _optional_text(data.tone)
    if data.selected_model is not None:
        comic.selected_model = _optional_text(data.selected_model)
    if data.status is not None:
        _validate_status(data.status, allowed=COMIC_STATUSES, field_name="status")
        comic.status = data.status

    await session.flush()
    await session.refresh(comic)
    return _comic_summary(comic)


async def archive_comic(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
) -> ComicSummary:
    return await update_comic(
        session,
        user_id=user_id,
        comic_id=comic_id,
        data=ComicUpdate(status=COMIC_STATUS_ARCHIVED),
    )


async def list_comics(
    session: AsyncSession,
    *,
    user_id: UUID,
    include_archived: bool = False,
) -> list[ComicSummary]:
    query = select(Comic).where(Comic.user_id == user_id)
    if not include_archived:
        query = query.where(Comic.status != COMIC_STATUS_ARCHIVED)
    result = await session.execute(
        query.order_by(desc(Comic.updated_at), desc(Comic.id))
    )
    return [_comic_summary(comic) for comic in result.scalars()]


async def get_comic_detail(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
) -> ComicDetail:
    comic = await get_owned_comic(session, user_id=user_id, comic_id=comic_id)
    scenes = (
        await session.execute(
            select(ComicScene)
            .where(ComicScene.comic_id == comic.id)
            .order_by(ComicScene.position, ComicScene.id)
        )
    ).scalars()
    pages = (
        await session.execute(
            select(ComicPage)
            .where(ComicPage.comic_id == comic.id)
            .order_by(ComicPage.page_number, ComicPage.id)
        )
    ).scalars()
    return ComicDetail(
        comic=_comic_summary(comic),
        scenes=[_scene_summary(scene) for scene in scenes],
        pages=[_page_summary(page) for page in pages],
    )


async def replace_scenes(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
    scenes: list[SceneInput],
) -> list[SceneSummary]:
    comic = await get_owned_comic(session, user_id=user_id, comic_id=comic_id)
    _validate_unique_positive(
        [scene.position for scene in scenes],
        field_name="position",
    )

    await session.execute(
        update(ComicPage).where(ComicPage.comic_id == comic.id).values(scene_id=None)
    )
    await session.execute(delete(ComicScene).where(ComicScene.comic_id == comic.id))
    created = [
        ComicScene(
            comic_id=comic.id,
            position=scene.position,
            title=_optional_text(scene.title),
            description=_optional_text(scene.description),
            prompt=_required_text(
                scene.description or scene.title or "",
                field_name="description",
            ),
            dialogue=_optional_text(scene.dialogue),
            caption=_optional_text(scene.caption),
            script_text=_optional_text(scene.dialogue),
        )
        for scene in sorted(scenes, key=lambda item: item.position)
    ]
    session.add_all(created)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise _conflict_error("Scene positions must be unique.") from exc
    return [_scene_summary(scene) for scene in created]


async def replace_pages(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
    pages: list[PageInput],
) -> list[PageSummary]:
    comic = await get_owned_comic(session, user_id=user_id, comic_id=comic_id)
    _validate_unique_positive(
        [page.page_number for page in pages],
        field_name="page_number",
    )
    await _validate_scene_ids(session, comic_id=comic.id, pages=pages)

    await session.execute(delete(ComicPage).where(ComicPage.comic_id == comic.id))
    created = [
        ComicPage(
            comic_id=comic.id,
            scene_id=page.scene_id,
            page_number=page.page_number,
            status=_validated_page_status(page.status),
            model=_optional_text(page.model),
            coin_cost=_validate_coin_cost(page.coin_cost),
            image_url=_optional_text(page.image_url),
            storage_key=_optional_text(page.storage_key),
            width=page.width,
            height=page.height,
            generated_at=page.generated_at,
        )
        for page in sorted(pages, key=lambda item: item.page_number)
    ]
    session.add_all(created)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise _conflict_error("Page numbers must be unique.") from exc
    return [_page_summary(page) for page in created]


async def get_owned_comic(
    session: AsyncSession,
    *,
    user_id: UUID,
    comic_id: UUID,
) -> Comic:
    result = await session.execute(
        select(Comic).where(Comic.id == comic_id, Comic.user_id == user_id)
    )
    comic = result.scalar_one_or_none()
    if comic is None:
        raise ApiError(
            status_code=404,
            code="COMIC_NOT_FOUND",
            message="Comic was not found.",
        )
    return comic


async def _validate_scene_ids(
    session: AsyncSession,
    *,
    comic_id: UUID,
    pages: list[PageInput],
) -> None:
    scene_ids = {page.scene_id for page in pages if page.scene_id is not None}
    if not scene_ids:
        return
    result = await session.execute(
        select(ComicScene.id).where(
            ComicScene.comic_id == comic_id,
            ComicScene.id.in_(scene_ids),
        )
    )
    owned_scene_ids = set(result.scalars())
    if owned_scene_ids != scene_ids:
        raise ApiError(
            status_code=400,
            code="COMIC_SCENE_INVALID",
            message="Page scene must belong to the comic.",
        )


def _comic_summary(comic: Comic) -> ComicSummary:
    return ComicSummary(
        id=comic.id,
        title=comic.title,
        story=comic.story,
        characters=comic.characters,
        style=comic.style or comic.style_preset,
        tone=comic.tone,
        selected_model=comic.selected_model,
        status=comic.status,
        created_at=comic.created_at,
        updated_at=comic.updated_at,
    )


def _scene_summary(scene: ComicScene) -> SceneSummary:
    return SceneSummary(
        id=scene.id,
        position=scene.position,
        title=scene.title,
        description=scene.description or scene.prompt,
        dialogue=scene.dialogue or scene.script_text,
        caption=scene.caption,
        created_at=scene.created_at,
        updated_at=scene.updated_at,
    )


def _page_summary(page: ComicPage) -> PageSummary:
    return PageSummary(
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


def _required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ApiError(
            status_code=400,
            code="COMIC_VALIDATION_ERROR",
            message=f"{field_name} is required.",
        )
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_status(
    status: str,
    *,
    allowed: set[str],
    field_name: str,
) -> None:
    if status not in allowed:
        raise ApiError(
            status_code=400,
            code="COMIC_STATUS_INVALID",
            message=f"{field_name} is invalid.",
        )


def _validated_page_status(status: str) -> str:
    _validate_status(status, allowed=PAGE_STATUSES, field_name="page status")
    return status


def _validate_unique_positive(values: list[int], *, field_name: str) -> None:
    if any(value < 1 for value in values):
        raise ApiError(
            status_code=400,
            code="COMIC_VALIDATION_ERROR",
            message=f"{field_name} must be greater than zero.",
        )
    if len(values) != len(set(values)):
        raise _conflict_error(f"{field_name} values must be unique.")


def _validate_coin_cost(value: int | None) -> int | None:
    if value is not None and value < 0:
        raise ApiError(
            status_code=400,
            code="COMIC_VALIDATION_ERROR",
            message="coin_cost must be greater than or equal to zero.",
        )
    return value


def _conflict_error(message: str) -> ApiError:
    return ApiError(status_code=409, code="COMIC_CONFLICT", message=message)
