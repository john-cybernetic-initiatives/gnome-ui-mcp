"""Tests for clipboard read/write via wl-copy/wl-paste."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from gnome_ui_mcp.desktop import input as input_mod


class TestClipboardRead:
    def test_read_returns_text(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_read",
            return_value={
                "success": True,
                "text": "hello world",
                "selection": "clipboard",
                "mime_type": "text/plain",
            },
        ) as remote_read:
            result = input_mod.clipboard_read()

        assert result["success"] is True
        assert result["text"] == "hello world"
        assert result["selection"] == "clipboard"
        remote_read.assert_called_once_with("text/plain")

    def test_read_empty_clipboard(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_read",
            return_value={
                "success": True,
                "text": None,
                "selection": "clipboard",
                "mime_type": "text/plain",
            },
        ):
            result = input_mod.clipboard_read()

        assert result["success"] is True
        assert result["text"] is None

    def test_read_primary_selection(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "primary text"
        with (
            patch("shutil.which", return_value="/usr/bin/wl-paste"),
            patch.object(subprocess, "run", return_value=mock_result) as mock_run,
        ):
            result = input_mod.clipboard_read(selection="primary")

        cmd = mock_run.call_args.args[0]
        assert "--primary" in cmd
        assert result["selection"] == "primary"

    def test_read_invalid_selection_raises(self) -> None:
        with pytest.raises(ValueError, match="selection"):
            input_mod.clipboard_read(selection="invalid")

    def test_read_missing_binary(self) -> None:
        with patch("shutil.which", return_value=None):
            result = input_mod.clipboard_read(selection="primary")

        assert result["success"] is False
        assert "wl-paste" in result["error"]


class TestClipboardWrite:
    def test_write_success(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={
                "success": True,
                "text_length": 5,
                "selection": "clipboard",
                "mime_type": "text/plain",
            },
        ) as remote_write:
            result = input_mod.clipboard_write("hello")

        assert result["success"] is True
        assert result["text_length"] == 5
        assert result["selection"] == "clipboard"
        remote_write.assert_called_once_with("hello", "text/plain")

    def test_write_does_not_block(self) -> None:
        """Mutter clipboard ownership is established without a helper process."""
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={"success": True},
        ) as remote_write:
            result = input_mod.clipboard_write("data")

        assert result["success"] is True
        remote_write.assert_called_once_with("data", "text/plain")

    def test_write_primary_selection(self) -> None:
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        with (
            patch("shutil.which", return_value="/usr/bin/wl-copy"),
            patch.object(subprocess, "Popen", return_value=mock_proc) as mock_popen,
        ):
            result = input_mod.clipboard_write("text", selection="primary")

        cmd = mock_popen.call_args.args[0]
        assert "--primary" in cmd
        assert result["selection"] == "primary"

    def test_write_invalid_selection_raises(self) -> None:
        with pytest.raises(ValueError, match="selection"):
            input_mod.clipboard_write("text", selection="invalid")

    def test_write_missing_binary(self) -> None:
        with patch("shutil.which", return_value=None):
            result = input_mod.clipboard_write("text", selection="primary")

        assert result["success"] is False
        assert "wl-copy" in result["error"]

    def test_write_empty_string(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={
                "success": True,
                "text_length": 0,
                "selection": "clipboard",
                "mime_type": "text/plain",
            },
        ):
            result = input_mod.clipboard_write("")

        assert result["success"] is True
        assert result["text_length"] == 0
