from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, model_validator

from app.core.config import Settings, get_settings
from app.services.current_user import CurrentUserContext, get_current_user
from app.services.openrouter import OpenRouterService

router = APIRouter(prefix="/ai-text", tags=["ai-text"])
CurrentUserDep = Annotated[CurrentUserContext, Depends(get_current_user)]


class AiTextRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task: str
    story: str
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    language: str | None = None
    page_count: int | None = None
    pages_total: int | None = None
    selected_scene: str | None = None
    scene_title: str | None = None
    scene_description: str | None = None
    scenes: list[str] | None = None
    dialogue: str | None = None
    caption: str | None = None
    layout: str | None = None
    previous_pages_context: list[str] | None = None
    model_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_creator_aliases(cls, value):
        if isinstance(value, dict):
            normalized = dict(value)
            if "selectedScene" in normalized and "selected_scene" not in normalized:
                normalized["selected_scene"] = normalized["selectedScene"]
            if "sceneTitle" in normalized and "scene_title" not in normalized:
                normalized["scene_title"] = normalized["sceneTitle"]
            if (
                "sceneDescription" in normalized
                and "scene_description" not in normalized
            ):
                normalized["scene_description"] = normalized["sceneDescription"]
            if "pageCount" in normalized and "page_count" not in normalized:
                normalized["page_count"] = normalized["pageCount"]
            if "pagesTotal" in normalized and "pages_total" not in normalized:
                normalized["pages_total"] = normalized["pagesTotal"]
            if (
                "previousPagesContext" in normalized
                and "previous_pages_context" not in normalized
            ):
                normalized["previous_pages_context"] = normalized[
                    "previousPagesContext"
                ]
            if "model" in normalized and "model_id" not in normalized:
                normalized["model_id"] = normalized["model"]
            return normalized
        return value

    def provider_payload(self) -> dict[str, Any]:
        return {
            "story": self.story,
            "characters": self.characters,
            "style": self.style,
            "tone": self.tone,
            "language": self.language,
            "page_count": self.page_count,
            "pages_total": self.pages_total,
            "selected_scene": self.selected_scene,
            "scene_title": self.scene_title,
            "scene_description": self.scene_description,
            "scenes": self.scenes,
            "dialogue": self.dialogue,
            "caption": self.caption,
            "layout": self.layout,
            "previous_pages_context": self.previous_pages_context,
        }


class AiTextResponse(BaseModel):
    text: str
    model: str
    scenes: list[str] | None = None
    characters: list[dict[str, Any]] | None = None
    pages: list[dict[str, Any]] | None = None


def get_text_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OpenRouterService:
    return OpenRouterService(settings)


@router.post("", response_model=AiTextResponse)
async def create_ai_text(
    payload: AiTextRequest,
    _current_user: CurrentUserDep,
    service: Annotated[OpenRouterService, Depends(get_text_service)],
) -> AiTextResponse:
    result = await service.generate_text(
        task=payload.task,
        payload=payload.provider_payload(),
        model=payload.model_id,
    )
    parsed = _parse_json_list(result.text)
    return AiTextResponse(
        text=result.text,
        model=result.model,
        scenes=_scene_strings(parsed) if payload.task == "scenes" else None,
        characters=_dict_items(parsed) if payload.task == "characters" else None,
        pages=_dict_items(parsed) if payload.task == "pagePlan" else None,
    )


def _parse_json_list(text: str) -> list[Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    return parsed


def _scene_strings(parsed: list[Any] | None) -> list[str] | None:
    if parsed is None:
        return None
    scenes: list[str] = []
    for item in parsed:
        if isinstance(item, str):
            scenes.append(item)
        elif isinstance(item, dict):
            value = item.get("description") or item.get("title")
            if value:
                scenes.append(str(value))
    return scenes or None


def _dict_items(parsed: list[Any] | None) -> list[dict[str, Any]] | None:
    if parsed is None:
        return None
    items = [item for item in parsed if isinstance(item, dict)]
    return items or None
