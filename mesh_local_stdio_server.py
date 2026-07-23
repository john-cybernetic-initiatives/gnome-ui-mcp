#!/usr/bin/env python3
"""Filtered stdio launcher for local Codex use."""

from gnome_ui_mcp.server import run
from mesh_authenticated_server import create_filtered_server


def main() -> None:
    run(transport="stdio", server=create_filtered_server())


if __name__ == "__main__":
    main()
