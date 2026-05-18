# Audit active stack source of truth and lifecycle projection

## Problem Definition

Active stack state should come from one authoritative projection rather than file walking or duplicate prompt builders. P180 must map where the active stack is written, read, finalized, and guarded.

## Proposed Solution

Inspect Cortex active-stack projection code, lifecycle API call sites, runtime Cortex handlers, and source-guard tests. Confirm production paths use the operational-store projection and that old file-walk collectors are absent. Run focused Cortex active-stack and lifecycle tests.

## Acceptance Criteria

- Active stack source of truth is identified.
- Write/read/finalize call sites are mapped.
- Source guardrails against file-walk stack collection are verified.
- Any stale bypass is fixed or escalated as a child/follow-up.

## Verification Plan

Use `rg` and targeted source reads for active-stack projection functions and stack collection strings. Run Cortex tests for `active_stack_projection`, context-event skill lifecycle, context status/read source guards, and operational-store roundtrip.

## Risks

- Active stack state may cross Cortex API and runtime handler boundaries, so overly narrow tests could miss an integration path.

## Assumptions

- This child problem focuses on active stack source/projection, not final LLM ordering or display-media behavior.
