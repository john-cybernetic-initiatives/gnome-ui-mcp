# Agent guide

This repository is an MCP server and CLI for automating a GNOME Wayland
desktop through AT-SPI (discovery) and Mutter RemoteDesktop (input).

## Commands

- `./scripts/check.sh` — full verification suite (sync, lint, format, tests).
- `uv run pytest tests -q` — run all tests.
- `uv run pytest path/to/test.py -q` — run a single test file.
- `uv run ruff check src tests scripts` — lint.
- `uv run ruff format src tests scripts` — format.
- `uv run python scripts/generate_docs.py` — regenerate the tool reference
  after changing tool definitions.

## Rules for Python

- Do not use `Any`, bare `except:`, `cast(...)`, or `# type: ignore`.
- Tools are declarations (`define_tool`); handlers return `None` and mutate
  the `McpResponse`. Layering is strict and one-directional:
  `tools/ -> adapters/ -> desktop/ -> runtime/gi_env.py`.
- Desktop modules return `{"success": bool, ...}` and never raise across the
  boundary; adapters flip failures into exceptions; the dispatcher in
  `server.py` formats them.

## Navigation workflow (preferred)

Drive the desktop snapshot-first — take a snapshot, then act on uids:

1. `take_snapshot` — capture the active window (or pass `window` from
   `list_windows`, or `app_name`). Returns a compact tree where every element
   has a stable `uid` like `7_42`.
2. `click` / `fill` / `hover` / `fill_form` — reference elements by `uid`.
   Actions auto-wait for the UI to settle and report effect verification.
   Pass `include_snapshot=true` to see the result in the same turn.
3. If a uid is rejected as stale (the UI changed), call `take_snapshot`
   again and use a fresh uid. uids are only valid for the latest snapshot.

`select_window` sets the implicit snapshot scope. The lower-level path-based
tools (`find_elements`, `click_element`, `set_element_text`, ...) remain
available as advanced building blocks.

See `docs/design-principles.md` and `docs/architecture.md` for the full model.

## Mesh maintenance fork

- Read `MAINTAINING.md` before changing fork-only code, dependencies, tags,
  remotes, authentication, or deployment behavior.
- Keep the original repository configured as the `upstream` remote. The
  maintainer-owned fork is `origin`.
- Treat `mesh-fork.toml` as the machine-readable source of truth for upstream
  provenance, the maintenance tag, tool policy, and capability versions.
- Fork releases use `mesh-v<upstream-version>-<patch>` tags. Do not create an
  upstream-style `v*` tag from a maintenance branch because that triggers the
  upstream registry, image, and Pages release workflow.
- Preserve the upstream `uv.lock`. Install the fork capability layer only from
  `requirements/mesh-capabilities.txt`, after upstream frozen checks pass.
- Run `./scripts/check.sh` before installing the capability layer. After the
  layer is installed, run `./scripts/check-mesh.sh`; do not run an unfrozen
  `uv sync` or `uv run` that can rewrite the upstream lock or remove the layer.
- Keep reusable GNOME compatibility fixes in this fork. Keep bearer-token
  rotation, broker catalogs, and MeshCentral node authorization in the
  `mesh-central` repository. Never commit credentials or token values.
- Every fork patch needs a regression test and an entry in
  `CHANGELOG.mesh.md`. Update the pinned commit in MeshCentral only after the
  fork branch is clean and the maintenance tag has been pushed.
