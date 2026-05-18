# Classify Runtime Legacy Execution Residue

## Problem Definition

P627 must classify runtime-wide direct execution/fallback/host/mount residue so stale compatibility code cannot hide outside the active shell handler path.

## Proposed Solution

Run exact scans over `novaic-agent-runtime` for subprocess/process/local/fallback/legacy/compat/host/mount and related shell execution terms, inspect representative production/test slices, classify hits as intended orchestration, test fixture, risky active bypass, or removable residue, and run a focused guard/test subset where available.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Representative production/test slices are cited.
- Every direct execution/fallback-looking production hit is classified.
- Risky active shell bypass creates a follow-up.
- Focused tests/guards pass or a coverage gap is recorded.

## Verification Plan

Run focused runtime guard tests that assert shell/tool boundary behavior and worker roster subprocess ownership.

## Risks

- `subprocess` is likely valid in service supervisor code; do not confuse worker process orchestration with user shell execution.
- Old PR-named tests may look like legacy residue while still guarding current behavior.

## Assumptions

- Active shell handler wiring was closed by P626.
