#!/usr/bin/env python3
"""Verify the fork-only dependency and tool-policy contract."""

from __future__ import annotations

import tomllib
from importlib.metadata import version
from pathlib import Path

from gnome_ui_mcp import server as server_module
from gnome_ui_mcp.tools.categories import ToolCategory

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    fork = tomllib.loads((PROJECT_ROOT / "mesh-fork.toml").read_text(encoding="utf-8"))
    capabilities = {name.lower(): value for name, value in fork["capabilities"].items()}
    installed = {name: version(name) for name in capabilities}
    if installed != capabilities:
        raise SystemExit(f"Capability versions do not match: {installed}")

    requirements = {
        name.strip().lower(): pinned.strip()
        for line in (PROJECT_ROOT / "requirements/mesh-capabilities.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        for name, pinned in [line.split("==", maxsplit=1)]
    }
    if requirements != capabilities:
        raise SystemExit("Capability manifest does not match mesh-fork.toml")

    upstream_tools = server_module.create_tools()
    excluded_tools = set(fork["excluded_tools"])
    filtered_tools = [tool for tool in upstream_tools if tool.name not in excluded_tools]
    names = {tool.name for tool in filtered_tools}
    categories = {tool.category for tool in filtered_tools}

    expected_tools = fork["expected_tools"]
    if len(names) != expected_tools:
        raise SystemExit(f"Expected {expected_tools} tools, found {len(names)}")
    if categories != set(ToolCategory) or len(categories) != fork["expected_categories"]:
        raise SystemExit("Filtered tool policy does not retain all categories")
    if excluded_tools & names:
        raise SystemExit("External-VLM tools remain in the filtered policy")

    print(
        "mesh-fork-ok "
        f"tools={len(names)} categories={len(categories)} capabilities={len(installed)}"
    )


if __name__ == "__main__":
    main()
