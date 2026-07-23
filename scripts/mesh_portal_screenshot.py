#!/usr/bin/env python3
"""Inspect or verify the scoped Screenshot portal capability for this fork.

This helper deliberately contains no MeshCentral credentials or endpoint state.
The broker invokes it in the graphical user's session after a confirmation-gated
plan.  A service which later uses the Screenshot portal must register the same
application identity for its own D-Bus connection.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.parse

from gi.repository import Gio, GLib

APP_ID = "ai.cyberneticinitiatives.GnomeUiMcp"
PERMISSION_TABLE = "screenshot"
PERMISSION_ID = "screenshot"
PERMISSION_VALUE = "yes"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "authorize"))
    return parser.parse_args(argv)


def dbus_proxy(
    connection: Gio.DBusConnection,
    name: str,
    object_path: str,
    interface: str,
) -> Gio.DBusProxy:
    return Gio.DBusProxy.new_sync(
        connection,
        Gio.DBusProxyFlags.NONE,
        None,
        name,
        object_path,
        interface,
        None,
    )


def property_value(proxy: Gio.DBusProxy, interface: str, name: str) -> int:
    result = proxy.call_sync(
        "Get",
        GLib.Variant("(ss)", (interface, name)),
        Gio.DBusCallFlags.NONE,
        5_000,
        None,
    )
    value = result.unpack()[0]
    if isinstance(value, GLib.Variant):
        value = value.unpack()
    return int(value)


def permission_values(permission_store: Gio.DBusProxy) -> list[str]:
    try:
        result = permission_store.call_sync(
            "GetPermission",
            GLib.Variant("(sss)", (PERMISSION_TABLE, PERMISSION_ID, APP_ID)),
            Gio.DBusCallFlags.NONE,
            5_000,
            None,
        )
    except GLib.Error:
        return []
    return list(result.unpack()[0])


def permission_variant() -> GLib.Variant:
    return GLib.Variant(
        "(sbssas)",
        (PERMISSION_TABLE, True, PERMISSION_ID, APP_ID, [PERMISSION_VALUE]),
    )


def screenshot_versions(connection: Gio.DBusConnection) -> tuple[int, int]:
    portal_properties = dbus_proxy(
        connection,
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.DBus.Properties",
    )
    store_properties = dbus_proxy(
        connection,
        "org.freedesktop.impl.portal.PermissionStore",
        "/org/freedesktop/impl/portal/PermissionStore",
        "org.freedesktop.DBus.Properties",
    )
    return (
        property_value(portal_properties, "org.freedesktop.portal.Screenshot", "version"),
        property_value(
            store_properties,
            "org.freedesktop.impl.portal.PermissionStore",
            "version",
        ),
    )


def wait_for_screenshot(
    connection: Gio.DBusConnection,
    screenshot: Gio.DBusProxy,
) -> pathlib.Path:
    token = "mesh_gnome_capture"
    sender = connection.get_unique_name().removeprefix(":").replace(".", "_")
    request_path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
    response: dict[str, object] = {}
    loop = GLib.MainLoop()

    def on_response(
        _connection: Gio.DBusConnection,
        _sender: str,
        _path: str,
        _interface: str,
        _signal: str,
        parameters: GLib.Variant,
        _data: object,
    ) -> None:
        code, results = parameters.unpack()
        response["code"] = code
        response["results"] = results
        loop.quit()

    def on_timeout() -> bool:
        response["timeout"] = True
        loop.quit()
        return False

    subscription = connection.signal_subscribe(
        "org.freedesktop.portal.Desktop",
        "org.freedesktop.portal.Request",
        "Response",
        request_path,
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
        None,
    )
    timeout = GLib.timeout_add_seconds(20, on_timeout)
    try:
        options = {
            "handle_token": GLib.Variant("s", token),
            "interactive": GLib.Variant("b", False),
        }
        screenshot.call_sync(
            "Screenshot",
            GLib.Variant("(sa{sv})", ("", options)),
            Gio.DBusCallFlags.NONE,
            5_000,
            None,
        )
        loop.run()
    finally:
        GLib.source_remove(timeout)
        connection.signal_unsubscribe(subscription)

    if response.get("timeout") or response.get("code") != 0:
        raise RuntimeError("The Screenshot portal did not return an approved screenshot")
    results = response.get("results")
    if not isinstance(results, dict):
        raise RuntimeError("The Screenshot portal returned no result dictionary")
    uri = str(results.get("uri", ""))
    screenshot_path = pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(uri).path))
    if not screenshot_path.is_file():
        raise RuntimeError("The Screenshot portal returned no screenshot file")
    return screenshot_path


def run(action: str) -> dict[str, object]:
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    screenshot_version, permission_store_version = screenshot_versions(connection)
    permission_store = dbus_proxy(
        connection,
        "org.freedesktop.impl.portal.PermissionStore",
        "/org/freedesktop/impl/portal/PermissionStore",
        "org.freedesktop.impl.portal.PermissionStore",
    )
    result: dict[str, object] = {
        "status": "portal-preflight",
        "screenshotVersion": screenshot_version,
        "permissionStoreVersion": permission_store_version,
        "permissions": permission_values(permission_store),
    }
    if action == "preflight":
        return result

    registry = dbus_proxy(
        connection,
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.host.portal.Registry",
    )
    registry.call_sync(
        "Register",
        GLib.Variant("(sa{sv})", (APP_ID, {})),
        Gio.DBusCallFlags.NONE,
        5_000,
        None,
    )
    permission_store.call_sync(
        "SetPermission",
        permission_variant(),
        Gio.DBusCallFlags.NONE,
        5_000,
        None,
    )
    if permission_values(permission_store) != [PERMISSION_VALUE]:
        raise RuntimeError("The Screenshot permission store did not retain the scoped grant")

    screenshot = dbus_proxy(
        connection,
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.portal.Screenshot",
    )
    screenshot_path = wait_for_screenshot(connection, screenshot)
    screenshot_path.unlink()
    result.update(
        {
            "status": "portal-authorized",
            "permissions": permission_values(permission_store),
            "screenshotTest": "passed",
        }
    )
    return result


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    print(json.dumps(run(args.action), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
