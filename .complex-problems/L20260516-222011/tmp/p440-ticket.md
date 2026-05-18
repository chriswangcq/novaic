# Ticket: Final runtime bridge guard verification

## Problem Definition

After bridge inventory and cleanup, perform a final independent guard pass to ensure no stale runtime bridge/context projection bypass or raw tool-result projection leak remains.

## Proposed Solution

- Run repo scans for old runtime bridge helper names, materialized context endpoint usage, prepare-path bypass patterns, and raw media/base64 tool-result leakage.
- Save final guard artifacts and classify remaining hits.
- Run focused runtime and Cortex tests covering prepare path, materialized context projection, payload/tool-result projection, and shell artifact contracts.

## Acceptance Criteria

- Old broad runtime helper names are absent from runtime production/tests.
- Remaining `/v1/context/read|append|batch` hits are classified as materialized projection endpoints/tests/docs, not LLM prepare.
- Prepare-path guards pass.
- Tool-result/display/shell artifact tests pass.
- Any unresolved hit becomes a follow-up rather than being ignored.

## Verification Plan

- Run targeted `rg` scans and save artifacts.
- Run focused runtime and Cortex suites from P438/P439 plus shell/tool-output suites.

## Risks

- Generated ledger artifacts contain old strings; exclude them from source guard scans.

## Assumptions

- This is a verification ticket. It should patch only if it discovers a concrete missed residue.
