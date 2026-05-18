# Ticket: scan and fix ephemeral path / media payload leakage

## Problem Definition

The project previously had failures around ephemeral Cortex backing paths and media payloads leaking into LLM/tool context. Audit the repo for remaining `/tmp/novaic-cortex-sandbox-*`, `/cortex/ro` contract mismatches, base64 screenshot/media leakage, and tool-output contract bypasses.

## Proposed Solution

- Scan for ephemeral backing path guidance.
- Scan shell/display/device/media output contracts for raw base64 or large payload text leakage.
- Scan docs/tests for stale examples that tell agents to reuse `/tmp/novaic-cortex-sandbox-*`.
- Fix active code/docs/tests where found.

## Acceptance Criteria

- No active prompt/tool/doc path recommends reusing ephemeral sandbox backing paths.
- Device/media CLI outputs follow text + blob/artifact manifest contract instead of raw base64.
- Context/tool projection tests cover shell text truncation and display image projection.
- Focused tests/linters for changed code pass.

## Verification Plan

- Focused `rg` scans for `novaic-cortex-sandbox`, raw `screenshot` base64 fields, `base64`, `data:image`, and `blob://runtime-artifact` contract.
- Run relevant Python/TS tests for changed modules.

## Risk

Do not break legitimate base64 use inside provider APIs; distinguish internal transport from LLM/tool context output.
