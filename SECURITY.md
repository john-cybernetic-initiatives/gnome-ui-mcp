# Security policy for the maintenance fork

The latest published `mesh-v*` tag is the only supported fork release. The
fork does not provide security support for arbitrary branch tips or locally
modified deployments.

Report fork-specific vulnerabilities through GitHub's private vulnerability
reporting for the maintainer-owned fork. Report issues that reproduce on an
unmodified upstream release to the upstream project. Do not include bearer
tokens, private endpoint catalogs, desktop screenshots, or MeshCentral node
identifiers in an issue, pull request, test fixture, or diagnostic transcript.

The reviewed deployment boundary requires:

- authenticated HTTP bound only to `127.0.0.1`;
- a regular, service-user-owned bearer-token file with mode `0600`;
- access logs disabled so authorization headers cannot be recorded;
- lingering disabled so the service follows the graphical login session;
- external-VLM tools excluded unless a separate credential and data-handling
  review explicitly enables them;
- exact fork commits and capability versions rather than automatic updates.

Credential generation, rotation, private upload, broker catalog changes, and
rollback are MeshCentral operations and must remain confirmation-gated and
secret-safe.
