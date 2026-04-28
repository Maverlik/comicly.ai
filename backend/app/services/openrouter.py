from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import ApiError

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass(frozen=True)
class ComicImagePromptInput:
    story: str
    characters: str | None = None
    style: str | None = None
    tone: str | None = None
    page: int = 1
    selected_scene: str | None = None
    scenes: list[str] | None = None
    dialogue: str | None = None
    caption: str | None = None
    layout: str | None = None
    model_id: str | None = None


@dataclass(frozen=True)
class OpenRouterImageResult:
    image_source: str
    model: str
    text: str
    prompt: str
    response_payload: dict[str, Any]


@dataclass(frozen=True)
class OpenRouterTextResult:
    text: str
    model: str
    response_payload: dict[str, Any]


class OpenRouterService:
    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client

    def select_image_model(self, requested_model: str | None) -> str:
        return select_image_model(self._settings, requested_model)

    def build_image_prompt(self, payload: ComicImagePromptInput) -> str:
        return build_image_prompt(payload)

    async def generate_image(
        self,
        payload: ComicImagePromptInput,
    ) -> OpenRouterImageResult:
        model = self.select_image_model(payload.model_id)
        prompt = self.build_image_prompt(payload)
        body: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "modalities": (
                ["image", "text"] if model.startswith("google/") else ["image"]
            ),
            "image_config": {
                "aspect_ratio": self._settings.openrouter_image_aspect_ratio
            },
        }
        data = await self._call_chat_completions(body)
        image_source = extract_image_source(data)
        if not image_source:
            raise ApiError(
                status_code=502,
                code="OPENROUTER_MISSING_IMAGE",
                message="OpenRouter response did not include an image.",
            )
        return OpenRouterImageResult(
            image_source=image_source,
            model=model,
            text=extract_text(data),
            prompt=prompt,
            response_payload=data,
        )

    async def generate_text(
        self,
        *,
        task: str,
        payload: dict[str, Any],
        model: str | None = None,
    ) -> OpenRouterTextResult:
        messages = build_text_messages(task=task, payload=payload)
        selected_model = (model or self._settings.openrouter_default_text_model).strip()
        data = await self._call_chat_completions(
            {
                "model": selected_model,
                "messages": messages,
            }
        )
        text = extract_text(data)
        if not text:
            raise ApiError(
                status_code=502,
                code="OPENROUTER_EMPTY_TEXT",
                message="OpenRouter response did not include text.",
            )
        return OpenRouterTextResult(
            text=text,
            model=selected_model,
            response_payload=data,
        )

    async def _call_chat_completions(self, body: dict[str, Any]) -> dict[str, Any]:
        api_key = self._settings.openrouter_api_key
        if not api_key:
            raise ApiError(
                status_code=503,
                code="OPENROUTER_NOT_CONFIGURED",
                message="OpenRouter API key is not configured.",
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._settings.openrouter_site_url,
            "X-Title": self._settings.openrouter_app_name,
        }
        timeout = self._settings.openrouter_request_timeout_seconds
        try:
            if self._http_client is not None:
                response = await self._http_client.post(
                    OPENROUTER_CHAT_COMPLETIONS_URL,
                    headers=headers,
                    json=body,
                    timeout=timeout,
                )
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        OPENROUTER_CHAT_COMPLETIONS_URL,
                        headers=headers,
                        json=body,
                    )
        except httpx.TimeoutException as exc:
            raise ApiError(
                status_code=504,
                code="OPENROUTER_TIMEOUT",
                message="OpenRouter request timed out.",
            ) from exc
        except httpx.HTTPError as exc:
            raise ApiError(
                status_code=502,
                code="OPENROUTER_ERROR",
                message="OpenRouter request failed.",
            ) from exc

        data = _json_or_empty(response)
        if response.status_code >= 400:
            raise ApiError(
                status_code=502,
                code="OPENROUTER_ERROR",
                message="OpenRouter returned an error.",
            )
        return data


def select_image_model(settings: Settings, requested_model: str | None) -> str:
    model = (requested_model or settings.openrouter_default_image_model).strip()
    if model not in settings.openrouter_allowed_image_model_set:
        raise ApiError(
            status_code=400,
            code="MODEL_NOT_ALLOWED",
            message="Requested model is not allowed.",
        )
    return model


def build_image_prompt(payload: ComicImagePromptInput) -> str:
    tone_map = {
        "funny": "witty, expressive, energetic",
        "emotional": "emotional, dramatic, cinematic",
        "epic": "epic, high stakes, heroic",
    }
    scenes = payload.scenes or []
    if scenes:
        scenes_block = "Panel breakdown:\n" + "\n".join(
            f"{index}. {scene}" for index, scene in enumerate(scenes, start=1)
        )
    else:
        scenes_block = (
            "No panel breakdown was provided. Create a clear 4-6 panel sequence "
            "from the story."
        )

    current_page = f"Current page: {payload.page}."
    if payload.selected_scene:
        current_page = f"{current_page} Focus scene: {payload.selected_scene}."

    lines = [
        "Create a complete, publication-ready comic book page.",
        (
            "The page must contain 4-6 clearly bordered panels with polished "
            "composition, cinematic lighting, varied shot sizes, and readable "
            "speech bubbles placed inside panels."
        ),
        f"Story: {payload.story}",
        (
            f"Character reference: {payload.characters}"
            if payload.characters
            else (
                "If character references are not provided, design distinct "
                "characters and keep them visually consistent across panels."
            )
        ),
        f"Visual style: {payload.style or 'Anime'}.",
        f"Tone: {tone_map.get(payload.tone or '', payload.tone or 'emotional')}.",
        current_page,
        scenes_block,
        (
            "Key dialogue to include as speech bubbles, preserving speakers when "
            f"named: {payload.dialogue}"
            if payload.dialogue
            else (
                "If dialogue is not provided, write natural speech bubbles for "
                "the characters."
            )
        ),
        f"Scene caption: {payload.caption}" if payload.caption else "",
        f"Layout direction: {payload.layout}" if payload.layout else "",
        (
            "Keep character design consistent across panels. Avoid watermarks, "
            "UI chrome, page numbers, or any explanatory text outside the comic art."
        ),
    ]
    return "\n".join(line for line in lines if line)


def build_text_messages(*, task: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    task_config = _text_task_config(task)
    return [
        {"role": "system", "content": task_config["system"]},
        {"role": "user", "content": task_config["instruction"](payload)},
    ]


def extract_image_source(data: dict[str, Any]) -> str | None:
    message = data.get("choices", [{}])[0].get("message")
    if not isinstance(message, dict):
        return None

    for candidate in (
        _nested_get(message, ["images", 0, "image_url", "url"]),
        _nested_get(message, ["images", 0, "url"]),
        _nested_get(message, ["image_url", "url"]),
    ):
        if isinstance(candidate, str) and candidate:
            return candidate

    content = message.get("content")
    if isinstance(content, list):
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "image_url":
                image_url = part.get("image_url")
                if isinstance(image_url, str) and image_url:
                    return image_url
                if isinstance(image_url, dict) and image_url.get("url"):
                    return image_url["url"]
            if part.get("type") == "output_image" and (
                part.get("image_url") or part.get("url")
            ):
                return part.get("image_url") or part["url"]
            if part.get("type") == "image":
                source = part.get("source")
                if isinstance(source, dict) and source.get("data"):
                    media_type = source.get("media_type") or "image/png"
                    return f"data:{media_type};base64,{source['data']}"
                if part.get("image_url") or part.get("url"):
                    return part.get("image_url") or part["url"]
    return None


def extract_text(data: dict[str, Any]) -> str:
    message = data.get("choices", [{}])[0].get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(
            str(part.get("text", "")).strip()
            for part in content
            if (
                isinstance(part, dict)
                and part.get("type") == "text"
                and part.get("text")
            )
        ).strip()
    return ""


def _text_task_config(task: str) -> dict[str, Any]:
    tasks: dict[str, dict[str, Any]] = {
        "enhance": {
            "system": (
                "You improve comic story prompts. Return one concise paragraph, "
                "without markdown."
            ),
            "instruction": lambda payload: (
                f"Improve this comic story in a {payload.get('tone') or 'emotional'} "
                f"tone and {payload.get('style') or 'Anime'} style.\n\n"
                f"{payload.get('story') or ''}"
            ),
        },
        "dialogue": {
            "system": (
                "You write short comic speech bubbles. Return 1-4 short lines, "
                "without markdown."
            ),
            "instruction": lambda payload: (
                "Write dialogue for this comic scene.\n\n"
                f"Story: {payload.get('story') or ''}\n"
                f"Scene: {payload.get('selected_scene') or ''}"
            ),
        },
        "scenes": {
            "system": (
                "You split stories into comic panels. Return only a JSON array of "
                "short scene descriptions."
            ),
            "instruction": lambda payload: (
                "Split this story into 4-6 comic panels.\n\n"
                f"{payload.get('story') or ''}"
            ),
        },
        "pagePlan": {
            "system": (
                "You are a comic story editor. Return only a JSON array with exactly "
                'one object per page: {"page": 1, "summary": "2-4 sentence page arc"}.'
            ),
            "instruction": lambda payload: (
                "Split this story into "
                f"{_page_total(payload)} "
                "sequential comic pages. Do not repeat the same event across pages.\n\n"
                f"Story: {payload.get('story') or ''}\n"
                f"Characters: {payload.get('characters') or ''}\n"
                f"Style: {payload.get('style') or 'Anime'}."
            ),
        },
        "continue": {
            "system": (
                "You continue comic stories. Return one concise paragraph for the next "
                "page only, without markdown."
            ),
            "instruction": lambda payload: (
                f"Original story: {payload.get('story') or ''}\n"
                f"Characters: {payload.get('characters') or ''}\n"
                "Previous pages:\n"
                + _previous_pages_block(payload.get("previous_pages_context"))
                + f"\nLanguage: {payload.get('language') or 'ru'}."
            ),
        },
        "summarize": {
            "system": (
                "You summarize one comic page in 1-2 factual sentences. Return plain "
                "text only."
            ),
            "instruction": lambda payload: (
                f"Page story: {payload.get('story') or ''}\n"
                f"Characters: {payload.get('characters') or ''}\n"
                f"Scenes: {payload.get('scene_description') or ''}\n"
                f"Dialogue: {payload.get('dialogue') or ''}"
            ),
        },
        "characters": {
            "system": (
                "You design comic characters. Return only a JSON array of 1-4 objects "
                'like {"name": "", "description": "specific visual description"}. '
                "Do not invent names when the story has no names."
            ),
            "instruction": lambda payload: (
                f"Story: {payload.get('story') or ''}\n"
                f"Style: {payload.get('style') or 'Anime'}.\n"
                "Extract only the main characters that are actually present. "
                "Make descriptions concrete enough for visual consistency."
            ),
        },
        "caption": {
            "system": (
                "You write compact comic panel captions. Return one caption, "
                "without markdown."
            ),
            "instruction": lambda payload: (
                "Write one caption for this comic scene.\n\n"
                f"{payload.get('selected_scene') or payload.get('story') or ''}"
            ),
        },
    }
    if task not in tasks:
        raise ApiError(
            status_code=400,
            code="AI_TEXT_TASK_INVALID",
            message="AI text task is invalid.",
        )
    return tasks[task]


def _page_total(payload: dict[str, Any]) -> int:
    try:
        return max(1, int(payload.get("pages_total") or payload.get("page_count") or 1))
    except (TypeError, ValueError):
        return 1


def _previous_pages_block(value: Any) -> str:
    if not isinstance(value, list) or not value:
        return "(none yet)"
    return "\n".join(
        f"Page {index}: {item}" for index, item in enumerate(value, start=1)
    )


def _nested_get(value: Any, path: list[str | int]) -> Any:
    current = value
    for item in path:
        if isinstance(item, int):
            if not isinstance(current, list) or len(current) <= item:
                return None
            current = current[item]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(item)
    return current


def _json_or_empty(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}
