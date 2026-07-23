"""Regression tests for GNOME compatibility fixes maintained by the fork."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.adapters import elements as elements_adapter
from gnome_ui_mcp.adapters import wayland as wayland_adapter
from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.desktop import screencast
from gnome_ui_mcp.desktop import wayland_info as wayland_info_mod


def test_focused_element_adapter_unwraps_desktop_envelope() -> None:
    element = {"id": "0/1/2", "name": "Controlled Input", "role": "entry"}
    with patch.object(
        elements_adapter._desktop_accessibility,
        "get_focused_element",
        return_value={"success": True, "element": element},
    ):
        assert elements_adapter.get_focused_element() == element


@pytest.mark.parametrize(
    ("module", "extra_arguments"),
    [
        (wayland_info_mod, {}),
        (wayland_adapter, {"check": False}),
    ],
)
def test_wayland_info_invokes_supported_cli(module, extra_arguments) -> None:
    completed = MagicMock(returncode=0, stdout="wl_compositor\nxdg_wm_base\n")
    with patch.object(module.subprocess, "run", return_value=completed) as run:
        module.list_protocols() if module is wayland_adapter else module.wayland_info()

    run.assert_called_once_with(
        ["/usr/bin/wayland-info"],
        capture_output=True,
        text=True,
        timeout=10,
        **extra_arguments,
    )


def test_screenshot_uses_screencast_fallback_on_dbus_denial(tmp_path: Path) -> None:
    output = tmp_path / "screenshot.png"

    def capture(path: Path) -> tuple[bool, str]:
        path.write_bytes(b"png")
        return True, str(path)

    with (
        patch.object(input_mod, "_validate_screenshot_path", return_value=output),
        patch.object(input_mod, "_screenshot_dbus", side_effect=RuntimeError("denied")),
        patch.object(input_mod, "_screenshot_via_screencast", side_effect=capture),
        patch.object(input_mod, "get_display_scale_factor", return_value=1),
        patch.object(input_mod, "Image", None),
    ):
        result = input_mod.screenshot()

    assert result["success"] is True
    assert result["path"] == str(output)


def test_screencast_fallback_extracts_first_frame(tmp_path: Path) -> None:
    recording = tmp_path / "recording.webm"
    recording.write_bytes(b"video")
    output = tmp_path / "screenshot.png"

    def extract(command, **_kwargs):
        Path(command[-1]).write_bytes(b"png")
        return MagicMock(returncode=0)

    with (
        patch.object(
            screencast,
            "screen_record_start",
            return_value={"success": True, "path": str(recording)},
        ) as start,
        patch.object(
            screencast,
            "screen_record_stop",
            return_value={"success": True, "path": str(recording)},
        ) as stop,
        patch.object(input_mod.time, "sleep") as sleep,
        patch.object(input_mod.subprocess, "run", side_effect=extract) as run,
        patch.object(input_mod, "_child_process_env", return_value={}),
    ):
        success, filename = input_mod._screenshot_via_screencast(output)

    assert success is True
    assert filename == str(output)
    assert output.read_bytes() == b"png"
    start.assert_called_once_with(framerate=10, draw_cursor=False)
    sleep.assert_called_once_with(0.8)
    stop.assert_called_once_with()
    assert run.call_args.args[0][0] == "/usr/bin/ffmpeg"


def test_screenshot_area_fallback_crops_using_display_scale(tmp_path: Path) -> None:
    output = tmp_path / "area.png"
    image = MagicMock()
    cropped = MagicMock()
    image.crop.return_value = cropped
    image_context = MagicMock()
    image_context.__enter__.return_value = image

    image_module = MagicMock()
    image_module.open.return_value = image_context

    with (
        patch.object(
            input_mod,
            "_screenshot_via_screencast",
            return_value=(True, str(output)),
        ),
        patch.object(input_mod, "get_display_scale_factor", return_value=2),
        patch.object(input_mod, "Image", image_module),
    ):
        success, filename = input_mod._screenshot_area_via_screencast(10, 20, 30, 40, output)

    assert success is True
    assert filename == str(output)
    image.crop.assert_called_once_with((20, 40, 80, 120))
    cropped.save.assert_called_once_with(str(output))
