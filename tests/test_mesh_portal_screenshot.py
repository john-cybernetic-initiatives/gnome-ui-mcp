from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "mesh_portal_screenshot.py"
SPEC = importlib.util.spec_from_file_location("mesh_portal_screenshot", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
portal_screenshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(portal_screenshot)


def test_portal_identity_is_fixed_and_scoped() -> None:
    assert portal_screenshot.APP_ID == "ai.cyberneticinitiatives.GnomeUiMcp"
    assert portal_screenshot.PERMISSION_TABLE == "screenshot"
    assert portal_screenshot.PERMISSION_ID == "screenshot"
    assert portal_screenshot.PERMISSION_VALUE == "yes"


def test_parse_args_accepts_only_reviewed_actions() -> None:
    assert portal_screenshot.parse_args(["preflight"]).action == "preflight"
    assert portal_screenshot.parse_args(["authorize"]).action == "authorize"


def test_property_value_accepts_unpacked_portal_properties() -> None:
    class Result:
        def unpack(self) -> tuple[int]:
            return (2,)

    class Proxy:
        def call_sync(self, *args: object) -> Result:
            return Result()

    assert portal_screenshot.property_value(Proxy(), "interface", "version") == 2


def test_permission_store_arguments_match_the_portal_signature() -> None:
    value = portal_screenshot.permission_variant()
    assert value.get_type_string() == "(sbssas)"
    assert value.unpack() == (
        "screenshot",
        True,
        "screenshot",
        "ai.cyberneticinitiatives.GnomeUiMcp",
        ["yes"],
    )
