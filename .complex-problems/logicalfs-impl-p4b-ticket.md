# Add LogicalFS Blob Boundary Guardrails

## Problem Definition

The current code now routes live Cortex `RO` / `RW` workspace operations through `CortexLogicalFileAuthority`, but the repository still contains allowed Blob byte APIs, transitional store adapter internals, tests, and stale documentation. A naive grep test would either miss real bypasses or block legitimate payload/display/audio/artifact Blob usage.

## Proposed Solution

Implement guardrails in a deliberately staged way:

1. Define the exact source allowlist and forbidden live-file bypass patterns.
2. Add a focused automated test or CI-adjacent script that scans runtime source files and rejects direct Blob object-store authority from Workspace/API/runtime/sandbox code.
3. Prove the guardrail both passes current allowed byte paths and would fail an obvious live `RO` / `RW` bypass shape.

## Acceptance Criteria

- Guardrails allow `blob://` and `/v1/blobs` for payload, display, audio, attachment, and artifact byte flows.
- Guardrails allow transitional persistence adapter internals only in explicitly named files.
- Guardrails reject obvious direct `/v1/objects`, `BlobCortexStore`, or Blob object-store authority from Workspace/API/runtime/sandbox execution code.
- Guardrails run as part of targeted tests or CI-accessible tests.

## Verification Plan

- Use the P006 audit as the allowlist baseline.
- Add tests/scripts and run the targeted Cortex and sandbox-service tests.
- Include a synthetic negative fixture or assertion so the guardrail is not merely testing the current tree.

## Risks

- Overbroad terms like `blob://` can break legitimate attachment/display/audio paths if the allowlist is not precise.
- Underbroad tests can give a false sense of safety while missing direct live `RO` / `RW` bypasses.
- Transitional adapter naming may need cleanup later; guardrails must not freeze stale architecture wording.

## Assumptions

- `CortexLogicalFileAuthority` is the only allowed Cortex live file authority boundary for `RO` / `RW`.
- Blob remains allowed for cheap byte objects and existing payload/display/audio/artifact flows.
- Transitional Blob object-store adapter internals are allowed only behind the authority boundary until the deeper LogicalFS service extraction replaces them.
