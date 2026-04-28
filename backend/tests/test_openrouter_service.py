import json
from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import ApiError
from app.services.openrouter import (
    ComicImagePromptInput,
    OpenRouterService,
    build_image_prompt,
    build_text_messages,
    extract_image_source,
    extract_text,
    select_image_model,
)

FIXTURES = Path("tests/fixtures")


class FakeOpenRouterClient:
    def __init__(self, response: httpx.Response | Exception) -> None:
        self.response = response
        self.requests: list[dict] = []

    async def post(self, url: str, **kwargs):
        self.requests.append({"url": url, **kwargs})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_select_image_model_uses_default_and_rejects_disallowed() -> None:
    settings = Settings(_env_file=None)

    assert select_image_model(settings, None) == settings.openrouter_default_image_model
    assert select_image_model(settings, "openai/gpt-5.4-image-2") == (
        "openai/gpt-5.4-image-2"
    )

    with pytest.raises(ApiError) as exc_info:
        select_image_model(settings, "not/allowed")

    assert exc_info.value.code == "MODEL_NOT_ALLOWED"


def test_build_image_prompt_includes_creator_context() -> None:
    prompt = build_image_prompt(
        ComicImagePromptInput(
            story="A kid finds a moon door.",
            characters="Mira, small astronaut",
            style="Manga",
            tone="epic",
            page=2,
            selected_scene="Door opens",
            scenes=["Discovery", "Launch"],
            dialogue="Mira: Let's go!",
            caption="A new orbit",
            layout="wide first panel",
        )
    )

    assert "publication-ready comic book page" in prompt
    assert "A kid finds a moon door." in prompt
    assert "Mira, small astronaut" in prompt
    assert "Door opens" in prompt
    assert "1. Discovery" in prompt
    assert "Mira: Let's go!" in prompt


def test_build_text_messages_rejects_unknown_task() -> None:
    with pytest.raises(ApiError) as exc_info:
        build_text_messages(task="unknown", payload={})

    assert exc_info.value.code == "AI_TEXT_TASK_INVALID"


def test_extracts_image_and_text_from_fixtures() -> None:
    image_payload = _fixture("openrouter_image_success.json")
    text_payload = _fixture("openrouter_text_success.json")

    assert extract_image_source(image_payload) == "https://example.com/generated.png"
    assert extract_text(image_payload) == "Image generated."
    assert extract_text(text_payload) == "A sharper comic story."


def test_extracts_data_url_image_part() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "media_type": "image/png",
                                "data": "aGVsbG8=",
                            },
                        }
                    ]
                }
            }
        ]
    }

    assert extract_image_source(payload) == "data:image/png;base64,aGVsbG8="


async def test_generate_image_maps_missing_image_to_typed_error(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    settings = Settings(_env_file=None)
    client = FakeOpenRouterClient(
        httpx.Response(200, json=_fixture("openrouter_missing_image.json"))
    )
    service = OpenRouterService(settings, http_client=client)

    with pytest.raises(ApiError) as exc_info:
        await service.generate_image(ComicImagePromptInput(story="Story"))

    assert exc_info.value.code == "OPENROUTER_MISSING_IMAGE"


async def test_openrouter_status_and_timeout_errors_are_typed(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    settings = Settings(_env_file=None)
    status_service = OpenRouterService(
        settings,
        http_client=FakeOpenRouterClient(httpx.Response(429, json={"error": "rate"})),
    )
    timeout_service = OpenRouterService(
        settings,
        http_client=FakeOpenRouterClient(httpx.TimeoutException("slow")),
    )

    with pytest.raises(ApiError) as status_exc:
        await status_service.generate_text(task="enhance", payload={"story": "Hi"})
    with pytest.raises(ApiError) as timeout_exc:
        await timeout_service.generate_text(task="enhance", payload={"story": "Hi"})

    assert status_exc.value.code == "OPENROUTER_ERROR"
    assert timeout_exc.value.code == "OPENROUTER_TIMEOUT"


async def test_openrouter_missing_key_is_typed(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    service = OpenRouterService(Settings(_env_file=None))

    with pytest.raises(ApiError) as exc_info:
        await service.generate_text(task="enhance", payload={"story": "Hi"})

    assert exc_info.value.code == "OPENROUTER_NOT_CONFIGURED"
