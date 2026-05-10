# Rewrite Final LogicalFS Architecture Docs

## Problem

Canonical docs still say registry uses `BlobCortexStore`, object-key docs still present `CortexLogicalFileAuthority`, and several docs imply Blob/Cortex owns live workspace files. This misleads future agents and humans.

## Success Criteria

- Canonical architecture docs describe final roles:
  - Cortex owns semantic scope/workspace concepts.
  - LogicalFS owns realtime `/ro` and `/rw`.
  - Blob stores cheap bytes/objects below LogicalFS and artifacts/display/download payloads.
  - sandboxd executes processes and receives mounted LogicalFS views.
- Stale canonical references to `CortexLogicalFileAuthority`, `BlobCortexStore`, and `blob_store.py` are removed or explicitly marked historical.
- Historical roadmap docs remain historical if edited minimally, but do not read as current canonical guidance.
