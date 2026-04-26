from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient
from starlette.routing import Mount

from app.main import create_app

PRIVATE_OR_FRONTEND_PATHS = [
    "/.env",
    "/.planning/PROJECT.md",
    "/backend/BACKEND_TZ.md",
    "/package.json",
    "/index.html",
    "/create.html",
    "/scripts/creator.js",
]

TRAVERSAL_PATHS = [
    "/../package.json",
    "/..%2Fpackage.json",
    "/%2e%2e/package.json",
    "/scripts/../package.json",
    "/backend/../.env",
]


async def test_private_root_and_frontend_paths_are_not_served(
    async_client: AsyncClient,
) -> None:
    for path in PRIVATE_OR_FRONTEND_PATHS:
        response = await async_client.get(path)

        assert response.status_code in {404, 405}, path
        assert "Comicly API" not in response.text


async def test_traversal_style_paths_are_not_served(
    async_client: AsyncClient,
) -> None:
    for path in TRAVERSAL_PATHS:
        response = await async_client.get(path)

        assert response.status_code in {400, 404, 405}, path
        assert "Comicly API" not in response.text


def test_backend_has_no_staticfiles_mount_or_file_server_route() -> None:
    app = create_app()

    assert not any(
        isinstance(route, Mount) and isinstance(route.app, StaticFiles)
        for route in app.routes
    )

    served_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/" not in served_paths
    assert "/{path:path}" not in served_paths
