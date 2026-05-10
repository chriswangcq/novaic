# Phase 4A Payload Manifest Boundary Audit

## Problem

Before wiring manifests, the current payload authority paths need a precise audit. `Workspace.write_payload`, `Workspace.read_payload`, step normalization, Blob adapter behavior, existing `OperationalSqliteStore` manifest methods, and tests must be mapped so implementation does not accidentally leave BlobRef as hidden semantic authority.

## Success Criteria

- All live payload write/read/externalization call sites are cataloged.
- Existing `payload_manifest` table/API fields are compared against the required semantic manifest contract.
- Local JSON payload behavior and external Blob payload behavior are classified separately.
- Missing/corrupt/fetch-failure behavior is identified with concrete current exceptions.
- Follow-on implementation child problems have explicit boundaries and no ambiguous payload authority source remains unclassified.

