"""Regression tests for the GNOME Wayland Mutter clipboard backend."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from gnome_ui_mcp.desktop import input as input_mod
from gnome_ui_mcp.runtime.gi_env import GLib


def test_read_own_mutter_selection_without_external_round_trip() -> None:
    remote = input_mod._MutterRemoteDesktopInput()
    proxy = MagicMock()
    remote._clipboard_is_owner = True
    remote._clipboard_payloads = {"text/plain": b"owned text"}

    with patch.object(remote, "_ensure_clipboard", return_value=proxy):
        result = remote.clipboard_read("text/plain")

    assert result == {
        "success": True,
        "text": "owned text",
        "selection": "clipboard",
        "mime_type": "text/plain",
    }
    proxy.call_with_unix_fd_list_sync.assert_not_called()


def test_read_external_mutter_selection_from_returned_fd() -> None:
    remote = input_mod._MutterRemoteDesktopInput()
    proxy = MagicMock()
    fd_list = MagicMock()
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"external text")
    os.close(write_fd)
    fd_list.get.return_value = read_fd
    proxy.call_with_unix_fd_list_sync.return_value = (
        GLib.Variant("(h)", (0,)),
        fd_list,
    )

    with patch.object(remote, "_ensure_clipboard", return_value=proxy):
        result = remote.clipboard_read("text/plain")

    assert result["success"] is True
    assert result["text"] == "external text"
    proxy.call_with_unix_fd_list_sync.assert_called_once()


def test_write_advertises_mutter_selection_and_keeps_payload() -> None:
    remote = input_mod._MutterRemoteDesktopInput()
    proxy = MagicMock()

    with patch.object(remote, "_ensure_clipboard", return_value=proxy):
        result = remote.clipboard_write("new text", "text/plain")

    assert result["success"] is True
    assert result["backend"] == "mutter-remote-desktop"
    assert remote._clipboard_is_owner is True
    assert remote._clipboard_payloads == {"text/plain": b"new text"}
    assert proxy.call_sync.call_args.args[0] == "SetSelection"


def test_selection_transfer_writes_payload_to_mutter_fd() -> None:
    remote = input_mod._MutterRemoteDesktopInput()
    proxy = MagicMock()
    fd_list = MagicMock()
    read_fd, write_fd = os.pipe()
    fd_list.get.return_value = write_fd
    proxy.call_with_unix_fd_list_sync.return_value = (
        GLib.Variant("(h)", (0,)),
        fd_list,
    )

    remote._serve_clipboard_transfer(proxy, 17, b"served text")

    assert os.read(read_fd, 64) == b"served text"
    os.close(read_fd)
    assert proxy.call_sync.call_args.args[0] == "SelectionWriteDone"
    assert proxy.call_sync.call_args.args[1].unpack() == (17, True)
