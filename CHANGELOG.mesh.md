# Mesh maintenance changelog

This file records fork-only changes. Upstream release history remains in
`CHANGELOG.md`.

## mesh-v0.5.0-3 — 2026-07-23

- Add hidden `.desktop` metadata for the portal application identity. The
  broker installs it in the selected user's applications directory before
  registering the identity; it does not expose an application launcher.

## mesh-v0.5.0-2 — 2026-07-23

- Add a bounded, broker-invoked Screenshot portal helper. It can inspect the
  portal, create a single app-scoped `screenshot/screenshot=yes` record for
  this fork identity, verify one non-interactive capture, and delete that
  test image. It contains no broker credentials or deployment state.

## mesh-v0.5.0-1 — 2026-07-22

- Add an authenticated loopback HTTP launcher and a filtered local stdio
  launcher with 113 tools across all 14 categories.
- Exclude only the two external-VLM tools, `analyze_screenshot` and
  `compare_screenshots`.
- Add a GNOME 49/50 screenshot fallback that extracts a frame from the already
  exposed GNOME Shell screencast capability instead of enabling unsafe mode.
- Correct Wayland protocol inspection for the installed `wayland-info` CLI.
- Correct focused-element adapter response unwrapping.
- Add a separately pinned OCR/media capability manifest and fork verification
  workflow.
