"""Scoped XDG Screenshot portal backend for the authenticated Mesh launcher."""

from __future__ import annotations

import secrets
import shutil
import stat
import threading
import urllib.parse
from pathlib import Path

from ..runtime.gi_env import Gio, GLib

APP_ID = "ai.cyberneticinitiatives.GnomeUiMcp"
PERMISSION_TABLE = "screenshot"
PERMISSION_ID = "screenshot"
PERMISSION_VALUE = "yes"
PORTAL_BUS = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SCREENSHOT_INTERFACE = "org.freedesktop.portal.Screenshot"
REGISTRY_INTERFACE = "org.freedesktop.host.portal.Registry"
PERMISSION_STORE_BUS = "org.freedesktop.impl.portal.PermissionStore"
PERMISSION_STORE_PATH = "/org/freedesktop/impl/portal/PermissionStore"
PERMISSION_STORE_INTERFACE = "org.freedesktop.impl.portal.PermissionStore"

_registration_lock = threading.Lock()
_registered_connection: str | None = None


def _proxy(
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


def _permission_values(permission_store: Gio.DBusProxy) -> list[str]:
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


def _register_application(connection: Gio.DBusConnection) -> None:
    global _registered_connection

    connection_name = connection.get_unique_name()
    with _registration_lock:
        if _registered_connection == connection_name:
            return
        registry = _proxy(
            connection,
            PORTAL_BUS,
            PORTAL_PATH,
            REGISTRY_INTERFACE,
        )
        registry.call_sync(
            "Register",
            GLib.Variant("(sa{sv})", (APP_ID, {})),
            Gio.DBusCallFlags.NONE,
            5_000,
            None,
        )
        _registered_connection = connection_name


def _request_screenshot(
    connection: Gio.DBusConnection,
    screenshot: Gio.DBusProxy,
) -> Path:
    token = f"gnome_ui_mcp_{secrets.token_hex(12)}"
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
        PORTAL_BUS,
        "org.freedesktop.portal.Request",
        "Response",
        request_path,
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
        None,
    )
    timeout_source = GLib.timeout_add_seconds(20, on_timeout)
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
        if not response.get("timeout"):
            GLib.source_remove(timeout_source)
        connection.signal_unsubscribe(subscription)

    if response.get("timeout"):
        raise RuntimeError("The Screenshot portal request timed out")
    if response.get("code") != 0:
        raise RuntimeError("The Screenshot portal denied the capture request")
    results = response.get("results")
    if not isinstance(results, dict):
        raise RuntimeError("The Screenshot portal returned no result dictionary")
    uri = str(results.get("uri", ""))
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "file":
        raise RuntimeError("The Screenshot portal returned an unsupported URI")
    source = Path(urllib.parse.unquote(parsed.path))
    try:
        metadata = source.lstat()
    except OSError as exc:
        raise RuntimeError("The Screenshot portal returned no screenshot file") from exc
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RuntimeError("The Screenshot portal returned an unsafe screenshot file")
    return source


def capture(output_path: Path) -> tuple[bool, str]:
    """Capture through the pre-authorized portal identity without changing policy."""
    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    permission_store = _proxy(
        connection,
        PERMISSION_STORE_BUS,
        PERMISSION_STORE_PATH,
        PERMISSION_STORE_INTERFACE,
    )
    if _permission_values(permission_store) != [PERMISSION_VALUE]:
        raise RuntimeError(
            f"Screenshot portal permission is not granted for {APP_ID}; "
            "run the broker authorization operation"
        )
    _register_application(connection)
    screenshot = _proxy(
        connection,
        PORTAL_BUS,
        PORTAL_PATH,
        SCREENSHOT_INTERFACE,
    )
    source = _request_screenshot(connection, screenshot)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, output_path)
    finally:
        source.unlink(missing_ok=True)
    if not output_path.is_file():
        raise RuntimeError("The Screenshot portal capture could not be stored")
    return True, str(output_path)
