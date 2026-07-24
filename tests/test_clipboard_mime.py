"""Tests for clipboard_read/clipboard_write with mime_type parameter."""

from __future__ import annotations

from unittest.mock import patch

from gnome_ui_mcp.desktop import input as input_mod


class TestClipboardReadMime:
    def test_read_custom_mime_text(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_read",
            return_value={
                "success": True,
                "text": "<html>hello</html>",
                "selection": "clipboard",
                "mime_type": "text/html",
            },
        ) as remote_read:
            result = input_mod.clipboard_read(mime_type="text/html")

        remote_read.assert_called_once_with("text/html")
        assert result["success"] is True
        assert result["text"] == "<html>hello</html>"
        assert result["mime_type"] == "text/html"

    def test_read_binary_mime_returns_base64(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_read",
            return_value={
                "success": True,
                "data_base64": "iVBORw0KGgo=",
                "data_length": 8,
                "selection": "clipboard",
                "mime_type": "image/png",
            },
        ) as remote_read:
            result = input_mod.clipboard_read(mime_type="image/png")

        remote_read.assert_called_once_with("image/png")
        assert result["success"] is True
        assert "data_base64" in result
        assert result["data_length"] == 8
        assert result["mime_type"] == "image/png"

    def test_read_default_mime_is_text_plain(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_read",
            return_value={
                "success": True,
                "text": "hello",
                "selection": "clipboard",
                "mime_type": "text/plain",
            },
        ) as remote_read:
            result = input_mod.clipboard_read()

        remote_read.assert_called_once_with("text/plain")
        assert result["mime_type"] == "text/plain"


class TestClipboardWriteMime:
    def test_write_custom_mime_text(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={
                "success": True,
                "selection": "clipboard",
                "mime_type": "text/html",
            },
        ) as remote_write:
            result = input_mod.clipboard_write("<b>bold</b>", mime_type="text/html")

        remote_write.assert_called_once_with("<b>bold</b>", "text/html")
        assert result["success"] is True
        assert result["mime_type"] == "text/html"

    def test_write_binary_mime_decodes_base64(self) -> None:
        import base64

        raw_data = b"\x89PNG"
        b64_str = base64.b64encode(raw_data).decode("ascii")

        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={"success": True},
        ) as remote_write:
            result = input_mod.clipboard_write(b64_str, mime_type="image/png")

        remote_write.assert_called_once_with(b64_str, "image/png")
        assert result["success"] is True

    def test_write_default_mime_is_text_plain(self) -> None:
        with patch.object(
            input_mod._REMOTE_INPUT,
            "clipboard_write",
            return_value={
                "success": True,
                "mime_type": "text/plain",
            },
        ) as remote_write:
            result = input_mod.clipboard_write("hello")

        remote_write.assert_called_once_with("hello", "text/plain")
        assert result["mime_type"] == "text/plain"
