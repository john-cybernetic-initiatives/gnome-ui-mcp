#!/usr/bin/env python3
"""Authenticated, Codex-facing launcher for the pinned gnome-ui-mcp v0.5.0 source."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import os
import re
import stat
from pathlib import Path

import uvicorn
from mcp.server.lowlevel.server import Server
from starlette.types import ASGIApp, Receive, Scope, Send

from gnome_ui_mcp import server as server_module
from gnome_ui_mcp.tools.categories import ToolCategory

_BIND_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000
_EXPECTED_TOOL_COUNT = 113
_EXCLUDED_TOOLS = frozenset({"analyze_screenshot", "compare_screenshots"})
_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def load_bearer_token(token_file: str) -> str:
    path = Path(token_file)
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("The bearer-token path must be a regular file, not a symlink.")
    if metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
        raise RuntimeError(
            "The bearer-token file must be owned by the service user with mode 0600."
        )
    token = path.read_text(encoding="utf-8").strip()
    if not _TOKEN_PATTERN.fullmatch(token):
        raise RuntimeError(
            "The bearer-token file does not contain a valid 256-bit base64url token."
        )
    return token


class BearerAuthMiddleware:
    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode("ascii")

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            supplied = headers.get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self._expected):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [
                            (b"content-type", b"text/plain; charset=utf-8"),
                            (b"cache-control", b"no-store"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": b"Unauthorized"})
                return
        await self._app(scope, receive, send)


def create_filtered_server() -> Server:
    upstream_create_tools = server_module.create_tools
    upstream_tools = upstream_create_tools()
    upstream_names = {tool.name for tool in upstream_tools}
    if not _EXCLUDED_TOOLS.issubset(upstream_names):
        raise RuntimeError(
            "The pinned external-VLM tool set no longer matches the reviewed overlay."
        )

    filtered_tools = [tool for tool in upstream_tools if tool.name not in _EXCLUDED_TOOLS]
    if len(filtered_tools) != _EXPECTED_TOOL_COUNT:
        raise RuntimeError(
            "The pinned gnome-ui-mcp tool count no longer matches the reviewed overlay."
        )
    if {tool.category for tool in filtered_tools} != set(ToolCategory):
        raise RuntimeError(
            "The filtered server no longer retains every gnome-ui-mcp tool category."
        )

    server_module.create_tools = lambda: list(filtered_tools)
    try:
        return server_module.create_server()
    finally:
        server_module.create_tools = upstream_create_tools


def build_app(token_file: str) -> ASGIApp:
    token = load_bearer_token(token_file)
    server = create_filtered_server()
    return BearerAuthMiddleware(server_module.streamable_http_app(server), token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run authenticated gnome-ui-mcp on loopback.")
    parser.add_argument("--auth-token-file", required=True)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    return parser


def configure_runtime() -> None:
    os.environ.setdefault("GNOME_UI_MCP_SCREENSHOT_BACKEND", "portal")


async def serve(token_file: str, port: int) -> None:
    if not 1 <= port <= 65535:
        raise RuntimeError("The MCP port must be between 1 and 65535.")
    configure_runtime()
    config = uvicorn.Config(
        build_app(token_file),
        host=_BIND_HOST,
        port=port,
        log_level="info",
        access_log=False,
    )
    await uvicorn.Server(config).serve()


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(serve(args.auth_token_file, args.port))


if __name__ == "__main__":
    main()
