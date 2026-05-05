import argparse
import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class SmokeResult:
    name: str
    ok: bool
    detail: str


def fetch(url: str, timeout: float) -> tuple[int, str, dict[str, str]]:
    request = Request(url, headers={"User-Agent": "comicly-smoke/1.0"})
    opener = build_opener(NoRedirectHandler)
    try:
        with opener.open(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body, dict(response.headers)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body, dict(exc.headers)
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def check_frontend(frontend_url: str, timeout: float) -> SmokeResult:
    try:
        status, body, _headers = fetch(frontend_url, timeout)
    except RuntimeError as exc:
        return SmokeResult("frontend", False, str(exc))

    ok = status == 200 and "Comicly" in body
    return SmokeResult("frontend", ok, f"HTTP {status}")


def check_json_endpoint(
    api_base_url: str,
    path: str,
    expected_status: int,
    expected_key: str,
    timeout: float,
) -> SmokeResult:
    url = urljoin(api_base_url.rstrip("/") + "/", path.lstrip("/"))
    try:
        status, body, _headers = fetch(url, timeout)
    except RuntimeError as exc:
        return SmokeResult(path, False, str(exc))

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return SmokeResult(path, False, f"HTTP {status}, non-JSON response")

    ok = status == expected_status and expected_key in payload
    return SmokeResult(path, ok, f"HTTP {status}, keys={','.join(payload.keys())}")


def check_oauth_route(api_base_url: str, provider: str, timeout: float) -> SmokeResult:
    path = f"/api/v1/auth/{provider}/login"
    url = urljoin(api_base_url.rstrip("/") + "/", path.lstrip("/"))
    try:
        status, _body, headers = fetch(url, timeout)
    except RuntimeError as exc:
        return SmokeResult(path, False, str(exc))

    ok = status in {302, 303, 307, 308, 400, 429}
    location = headers.get("Location", "")
    detail = f"HTTP {status}"
    if location:
        detail = f"{detail}, redirect={location.split('?', 1)[0]}"
    return SmokeResult(path, ok, detail)


def print_result(result: SmokeResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.name}: {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Comicly deployment URLs.")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--frontend-url", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--skip-ready",
        action="store_true",
        help="Skip /ready when the target database is intentionally unavailable.",
    )
    args = parser.parse_args()

    results = [
        check_frontend(args.frontend_url, args.timeout),
        check_json_endpoint(args.api_base_url, "/health", 200, "status", args.timeout),
    ]
    if not args.skip_ready:
        results.append(
            check_json_endpoint(
                args.api_base_url, "/ready", 200, "status", args.timeout
            )
        )
    results.extend(
        [
            check_oauth_route(args.api_base_url, "google", args.timeout),
            check_oauth_route(args.api_base_url, "yandex", args.timeout),
        ]
    )

    for result in results:
        print_result(result)

    print(
        "[MANUAL] Live OAuth callbacks require provider credentials and browser login."
    )
    print("[MANUAL] Live generation requires auth, OpenRouter, S3 storage, and coins.")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
