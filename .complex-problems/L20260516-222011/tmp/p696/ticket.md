# Foundational service boundary classification for Blob LogicalFS and Sandbox

## Problem Definition

Classify Blob, LogicalFS, and Sandbox/Sandboxd as foundational infrastructure services. Verify their active entrypoints, launch evidence, dependency boundaries, and whether any code/docs still imply that Cortex owns file storage, realtime RO/RW authority, or sandbox execution internals.

## Proposed Solution

Use the P695 discovery artifacts plus targeted source inspection to produce a boundary map for each foundational service:

1. Blob: active service entrypoint, cheap file-store role, consumers, and boundaries against LogicalFS/Cortex.
2. LogicalFS: realtime logical RO/RW authority role, storage/backing dependencies, and whether it is exposed as a service/library boundary.
3. Sandbox/Sandboxd: execution service role, SDK/service split, and boundary against Cortex shell facade.
4. Cross-boundary residue: find and patch or record stale claims that collapse foundational responsibilities into Cortex.

## Acceptance Criteria

- Blob, LogicalFS, and Sandbox/Sandboxd each have entrypoint, launch evidence, role, and dependency boundary recorded.
- Cortex usages of Blob/LogicalFS/Sandbox are classified as client/facade usage rather than ownership unless code proves otherwise.
- Stale claims in docs/scripts/code comments that misrepresent the boundary are patched or explicitly recorded as residual risk.
- If files change, focused syntax/static/guard checks pass.

## Verification Plan

- Inspect P695 matrix and targeted source files for each foundational service.
- Produce a boundary-map artifact with evidence pointers.
- Run targeted stale-boundary scans for Cortex-owning-file/sandbox claims.
- Patch safe wording or guard gaps if found, then run relevant tests/lints.

## Risks

- LogicalFS may exist as both library/substrate and service concept; classification must not overclaim deployment state.
- Cortex has shell/workspace facade code and may legitimately orchestrate foundational services without owning them.
- Overzealous cleanup could remove valuable historical design docs or regression tests.

## Assumptions

- Backwards compatibility for misleading stale claims is not required.
- Safe docs/guard updates are in scope; large architectural rewrites should spawn follow-up tickets.
