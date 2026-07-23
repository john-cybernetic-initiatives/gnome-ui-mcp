# Maintaining the Mesh GNOME UI MCP fork

## Scope and provenance

This fork is a deliberately pinned native runtime for MeshCentral and local
Codex use. Its upstream base is:

- Repository: `https://github.com/asattelmaier/gnome-ui-mcp`
- Tag: `v0.5.0`
- Commit: `338029886449eb7aa212cd4076c1b574a18fb6fb`
- First fork release: `mesh-v0.5.0-1`

The same values are recorded in machine-readable form in `mesh-fork.toml`.
Update that file and this document together.

The maintained fork is
`https://github.com/john-cybernetic-initiatives/gnome-ui-mcp`.

The fork owns reusable GNOME compatibility fixes and the two launchers in the
repository root. MeshCentral continues to own credential rotation, endpoint
catalogs, node authorization, WebRelay integration, and deployment templates.
No credential value belongs in either repository.

## Remote layout

Use these remote roles consistently:

```text
origin    https://github.com/john-cybernetic-initiatives/gnome-ui-mcp.git
upstream  https://github.com/asattelmaier/gnome-ui-mcp.git
```

Never force-push a published maintenance tag. Never update an installed host
by pulling an unreviewed branch tip; deploy an exact, reviewed commit.

## Dependency model

The upstream environment and the capability layer are intentionally separate.
This preserves the reviewed upstream lock while providing OCR and media
features required by the native service.

For a fresh environment:

```bash
export UV_PYTHON=/usr/bin/python3
export UV_NO_MANAGED_PYTHON=1
export PATH="$HOME/.local/bin:/usr/bin:/bin"
./scripts/bootstrap.sh
./scripts/check.sh
./scripts/install-mesh-capabilities.sh
./scripts/check-mesh.sh
```

Do not run `scripts/check.sh`, `uv sync`, or `uv run` after installing the
capability layer unless you intend to restore the upstream-only environment.
Those commands may remove fork-only packages or change resolution state.

## Patch boundaries

Keep patches small and independently reviewable:

1. Generic GNOME compatibility fixes belong under `src/` with regression
   tests. Offer generally useful fixes back to upstream.
2. The authenticated HTTP and filtered stdio launchers may remain fork-only,
   but must contain no secret values or host-specific paths.
3. Capability versions belong only in
   `mesh-fork.toml` and the generated-compatible
   `requirements/mesh-capabilities.txt`. Fork verification requires the two
   files to agree exactly.
4. systemd units, autostart entries, runtime tokens, and Codex configuration
   are deployment state and must not be committed to this repository.

## Updating from upstream

1. Fetch without modifying the installed branch: `git fetch upstream --tags`.
2. Review upstream release notes and dependency changes.
3. Create a new branch from the exact upstream tag, for example
   `mesh/full-capabilities-v0.6.0`.
4. Reapply or cherry-pick each fork patch separately. Drop patches already
   accepted upstream.
5. Run the upstream checks before the capability install, then run the fork
   checks and a controlled GNOME session smoke test afterward.
6. Record changes in `CHANGELOG.mesh.md` and tag
   `mesh-v<upstream-version>-<patch>`.
7. Push the branch and tag, then update MeshCentral's expected commit and
   reviewed asset hashes in the same broker change.

## Release and rollback

A maintenance release is valid only when:

- the working tree is clean;
- upstream and fork checks pass;
- exactly 113 filtered tools and 14 categories are present;
- unauthenticated HTTP returns 401 and authenticated initialization succeeds;
- controlled focus, typing, screenshot, OCR, clipboard, Wayland, and recording
  smoke tests pass in a real graphical session;
- the installed service binds only to `127.0.0.1` and lingering remains off.

Rollback by selecting the previous signed-off `mesh-v*` tag, rebuilding the
virtual environment from the upstream lock, reinstalling the matching
capability manifest, and restarting the graphical-session user service. Token
rotation and broker catalog rollback remain MeshCentral operations.
