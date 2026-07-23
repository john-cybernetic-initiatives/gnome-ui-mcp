"""Security and policy tests for the Mesh transport launchers."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from mesh_authenticated_server import BearerAuthMiddleware, load_bearer_token

TOKEN = "A" * 43


def test_token_loader_requires_private_regular_file(tmp_path: Path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text(f"{TOKEN}\n", encoding="utf-8")
    token_file.chmod(0o600)
    assert load_bearer_token(str(token_file)) == TOKEN

    token_file.chmod(0o644)
    with pytest.raises(RuntimeError, match="mode 0600"):
        load_bearer_token(str(token_file))


def test_bearer_middleware_rejects_missing_authorization() -> None:
    app_called: list[bool] = []
    messages: list[dict] = []

    async def app(_scope, _receive, _send) -> None:
        app_called.append(True)

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    middleware = BearerAuthMiddleware(app, TOKEN)
    asyncio.run(middleware({"type": "http", "headers": []}, receive, send))

    assert app_called == []
    assert messages[0]["status"] == 401
    assert messages[0]["headers"] == [
        (b"content-type", b"text/plain; charset=utf-8"),
        (b"cache-control", b"no-store"),
    ]


def test_bearer_middleware_accepts_exact_token() -> None:
    app_called: list[bool] = []

    async def app(_scope, _receive, _send) -> None:
        app_called.append(True)

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_message: dict) -> None:
        return None

    middleware = BearerAuthMiddleware(app, TOKEN)
    headers = [(b"authorization", f"Bearer {TOKEN}".encode("ascii"))]
    asyncio.run(middleware({"type": "http", "headers": headers}, receive, send))

    assert app_called == [True]
