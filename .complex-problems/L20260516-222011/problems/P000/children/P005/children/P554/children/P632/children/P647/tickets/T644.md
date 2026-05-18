# Audit Sandbox Backing Path Residue

## Problem Definition

Shell and agent-facing filesystem contracts should expose stable `/cortex/ro`, `/cortex/rw`, `$RO`, and `$RW` paths, not ephemeral `novaic-cortex-sandbox-*` backing paths. Remaining references must be classified so old sandbox backing paths do not become contractual again.

## Proposed Solution

Scan for `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, and stable path contract terms. Inspect meaningful hits and classify them as defensive diagnostics, test fixtures, docs/history, or active path leak. Remove clear active leaks if found; otherwise record the classification.

## Acceptance Criteria

- Scan output is recorded.
- All meaningful ephemeral backing path hits are classified.
- No active user/agent-facing shell contract tells agents to reuse `/tmp/novaic-cortex-sandbox-*` paths.
- Any active leak becomes a follow-up or is fixed.

## Verification Plan

Run `rg` scans across Cortex/runtime/sandbox/logicalfs/app docs and inspect active code/test contexts. If changes are made, run affected tests.

## Risks

- Some defensive error messages may mention the forbidden backing path to tell agents not to use it; those are intended.
- Historical ledger artifacts may contain old bad outputs and should not be treated as runtime code.

## Assumptions

- Stable `/cortex/ro` and `/cortex/rw` are the correct exposed contract.
