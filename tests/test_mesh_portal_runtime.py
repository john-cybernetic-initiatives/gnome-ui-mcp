"""Regression tests for the scoped runtime Screenshot portal backend."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import portal_screenshot


def test_portal_capture_consumes_existing_grant_and_removes_returned_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "portal.png"
    source.write_bytes(b"portal-image")
    output = tmp_path / "cache" / "screenshot.png"
    connection = MagicMock()
    permission_store = MagicMock()
    screenshot = MagicMock()

    with (
        patch.object(
            portal_screenshot.Gio,
            "bus_get_sync",
            return_value=connection,
        ),
        patch.object(
            portal_screenshot,
            "_proxy",
            side_effect=[permission_store, screenshot],
        ),
        patch.object(
            portal_screenshot,
            "_permission_values",
            return_value=[portal_screenshot.PERMISSION_VALUE],
        ),
        patch.object(portal_screenshot, "_register_application") as register,
        patch.object(
            portal_screenshot,
            "_request_screenshot",
            return_value=source,
        ),
    ):
        success, filename = portal_screenshot.capture(output)

    assert success is True
    assert filename == str(output)
    assert output.read_bytes() == b"portal-image"
    assert not source.exists()
    register.assert_called_once_with(connection)


def test_portal_capture_refuses_missing_scoped_grant(tmp_path: Path) -> None:
    connection = MagicMock()
    permission_store = MagicMock()
    with (
        patch.object(
            portal_screenshot.Gio,
            "bus_get_sync",
            return_value=connection,
        ),
        patch.object(
            portal_screenshot,
            "_proxy",
            return_value=permission_store,
        ),
        patch.object(portal_screenshot, "_permission_values", return_value=[]),
        patch.object(portal_screenshot, "_register_application") as register,
    ):
        with pytest.raises(RuntimeError, match="permission is not granted"):
            portal_screenshot.capture(tmp_path / "screenshot.png")

    register.assert_not_called()
