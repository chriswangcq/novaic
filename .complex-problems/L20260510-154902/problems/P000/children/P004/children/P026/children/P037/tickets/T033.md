# Verify tool step cutover boundaries

## Problem Definition

P035 and P036 introduced explicit normalization and `ToolStepRecorded` emission, but P026 should not close until the remaining legacy step-file writes are statically audited and classified. The goal is to catch hidden direct-only tool-result write paths before later cleanup phases.

## Proposed Solution

- Run focused step event tests and the full Cortex suite.
- Use static scans to locate remaining writes to `steps/*.json`, `steps/_index.jsonl`, and `payloads/*.json`.
- Classify each remaining write as:
  - transitional projection behind the new event path;
  - payload store support required by event payload refs;
  - legacy direct-only bypass requiring a follow-up.
- Record the audit result in the ledger.

## Acceptance Criteria

- Test evidence confirms P035/P036 still pass.
- Static scan evidence identifies all obvious remaining step/payload write sites.
- No unclassified direct-only `steps_write` bypass remains.
- If a true gap is found, create a follow-up instead of declaring success.

## Verification Plan

- Run focused step event tests.
- Run full Cortex tests.
- Run `rg` scans for step and payload write patterns in Cortex.
- Review API and workspace paths touched by step writes.

## Risks

- Static scans can miss dynamic writes; mitigate by scanning both API call sites and Workspace low-level write helpers.

## Assumptions

- Legacy step files are still allowed only as transitional projection until later read-cutover/cleanup phases.
