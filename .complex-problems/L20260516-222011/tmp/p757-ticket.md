# Blob LogicalFS Sandbox VMuse service-code residue discovery ticket

## Problem Definition

Blob, LogicalFS, Sandbox, and VMuse service code may still contain stale fallback/compatibility paths, local-only shortcuts, raw media/base64 behavior, or outdated ownership wording that conflicts with the current Blob-backed artifact, LogicalFS realtime RO/RW, Sandbox service, and VMuse lower-level protocol boundaries.

## Proposed Solution

Split discovery by service family so each boundary can be scanned and classified independently: Blob service, LogicalFS service/core, Sandbox service/VMuse service, and app-bundled generated/resource copies where they mirror active code. Each child should identify exact remediation candidates without modifying code during discovery.

## Acceptance Criteria

- Blob service code is scanned and classified.
- LogicalFS code is scanned and classified.
- Sandbox service and VMuse code are scanned and classified.
- App resource/generated copies of VMuse/Sandbox-facing code are checked for stale duplicated residue if they are active shipped artifacts.
- Exact remediation candidates are listed with file pointers.
- No product code is modified in this discovery ticket.

## Verification Plan

Use bounded `rg --files`, focused residue searches, and spot reads for fallback/compat/local/direct/base64/media/artifact/blob/logicalfs/sandbox/vmuse terms. Split children must save or cite evidence artifacts and classify each suspicious family.

## Risks

- Lower-level services may legitimately handle bytes/base64 internally; only user/LLM-facing text leakage or stale ownership wording should be remediation candidates.
- Generated app resource copies may mirror source files; classify whether they require direct patching or regeneration.

## Assumptions

- Service code lives under `novaic-blob-service`, `novaic-logicalfs`, `novaic-sandbox-service`, `novaic-mcp-vmuse`, and possibly app resource copies.
