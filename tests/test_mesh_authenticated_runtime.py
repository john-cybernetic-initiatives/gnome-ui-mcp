"""Authenticated launcher runtime policy tests."""

from __future__ import annotations

import os
from unittest.mock import patch

from mesh_authenticated_server import configure_runtime


def test_authenticated_launcher_defaults_to_strict_portal_capture() -> None:
    with patch.dict(os.environ, {}, clear=True):
        configure_runtime()
        assert os.environ["GNOME_UI_MCP_SCREENSHOT_BACKEND"] == "portal"


def test_authenticated_launcher_preserves_explicit_backend_override() -> None:
    with patch.dict(
        os.environ,
        {"GNOME_UI_MCP_SCREENSHOT_BACKEND": "auto"},
        clear=True,
    ):
        configure_runtime()
        assert os.environ["GNOME_UI_MCP_SCREENSHOT_BACKEND"] == "auto"
