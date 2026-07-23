## Summary

Describe the upstream issue, fork-only requirement, or broker change addressed
by this pull request.

## Maintenance checklist

- [ ] Generic GNOME behavior has a regression test and is suitable for an
      upstream contribution.
- [ ] `./scripts/check.sh` passed before installing the capability layer.
- [ ] `./scripts/install-mesh-capabilities.sh` and
      `./scripts/check-mesh.sh` passed afterward.
- [ ] `mesh-fork.toml`, `requirements/mesh-capabilities.txt`,
      `MAINTAINING.md`, and `CHANGELOG.mesh.md` agree where applicable.
- [ ] Tool-policy changes retain the reviewed category and approval model.
- [ ] No bearer token, credential, host secret, or private endpoint catalog is
      present in the diff or test output.
- [ ] A controlled graphical-session smoke test was run for media, OCR, or
      input changes.
- [ ] MeshCentral's pinned commit and reviewed assets will be updated only
      after this branch is clean and its `mesh-v*` tag is pushed.
