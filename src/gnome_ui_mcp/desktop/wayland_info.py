from __future__ import annotations

import subprocess

from .types import JsonDict


def wayland_info(filter_protocol: str | None = None) -> JsonDict:
    try:
        result = subprocess.run(
            ["/usr/bin/wayland-info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return {"success": False, "error": "wayland-info not found. Install wayland-utils."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    if result.returncode != 0:
        return {"success": False, "error": f"wayland-info exited with code {result.returncode}"}

    protocols = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]

    if filter_protocol:
        protocols = [p for p in protocols if filter_protocol.lower() in p.lower()]

    return {
        "success": True,
        "protocols": protocols,
        "protocol_count": len(protocols),
    }
