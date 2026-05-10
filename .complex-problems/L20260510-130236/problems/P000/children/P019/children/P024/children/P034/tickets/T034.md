# Ticket: Rewrite Final LogicalFS Architecture Docs

## Problem Definition

Canonical docs still describe transitional Cortex/Blob live workspace ownership and old modules that no longer exist.

## Proposed Solution

Rewrite canonical Cortex/LogicalFS docs to state the final layering: Cortex semantic layer, LogicalFS realtime `/ro` and `/rw`, Blob cheap byte/object persistence below LogicalFS and artifact flows, sandboxd process execution. Update or mark historical roadmap docs so old names do not look current.

## Acceptance Criteria

- Canonical docs no longer mention `CortexLogicalFileAuthority`, `BlobCortexStore`, `workspace_files.py`, or `novaic_cortex/blob_store.py` as current architecture.
- Docs explain the final module boundaries and service relationships.
- Any old names left in roadmap docs are explicitly historical.

## Verification Plan

- Run doc residue scans for old names in canonical docs.
- Run broader scan to classify remaining historical roadmap references.

## Risks

- Over-editing old roadmap tickets can erase useful history; prefer a clear historical banner instead.

## Assumptions

- Current canonical docs are under `docs/cortex*` and `docs/architecture/*`.
