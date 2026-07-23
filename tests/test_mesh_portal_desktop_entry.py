from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

ENTRY = Path(__file__).parents[1] / "assets" / "ai.cyberneticinitiatives.GnomeUiMcp.desktop"


def test_portal_identity_desktop_entry_is_hidden_and_non_launching() -> None:
    parser = ConfigParser(interpolation=None)
    parser.read(ENTRY, encoding="utf-8")
    desktop = parser["Desktop Entry"]
    assert desktop["Type"] == "Application"
    assert desktop["NoDisplay"] == "true"
    assert desktop["Exec"] == "/usr/bin/true"
