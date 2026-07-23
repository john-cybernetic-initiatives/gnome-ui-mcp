# Mesh maintenance changelog

This file records fork-only changes. Upstream release history remains in
`CHANGELOG.md`.

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
