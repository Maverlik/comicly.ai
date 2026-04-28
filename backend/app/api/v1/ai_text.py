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

    def provider_payload(self) -> dict[str, Any]:
        return {
            "story": self.story,
            "characters": self.characters,
            "style": self.style,
            "tone": self.tone,
            "selected_scene": self.selected_scene,
            "scenes": self.scenes,
            "dialogue": self.dialogue,
            "caption": self.caption,
            "layout": self.layout,
        }


class AiTextResponse(BaseModel):
    text: str
    model: str
    scenes: list[str] | None = None


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
    return AiTextResponse(
        text=result.text,
        model=result.model,
        scenes=_parse_scenes(result.text) if payload.task == "scenes" else None,
    )


def _parse_scenes(text: str) -> list[str] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
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
