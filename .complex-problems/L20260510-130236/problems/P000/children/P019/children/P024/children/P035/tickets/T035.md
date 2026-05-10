# Ticket: Final Old Authority Cleanup Verification

## Problem Definition

After source deletion, guardrail tightening, and doc rewrite, the repository needs a final proof that behavior is intact and old authority residue is either gone or intentionally historical/guardrail-only.

## Proposed Solution

Run full package tests and final residue scans. If any unclassified live residue remains, record not_success and create follow-up rather than closing.

## Acceptance Criteria

- Full Cortex tests pass.
- LogicalFS tests pass.
- Sandbox-service tests pass.
- Source/tests canonical-doc residue scans are clean.
- Remaining old names, if any, are only guardrail forbidden patterns or historical roadmap text.

## Verification Plan

- Run `python3 -m pytest -q` in `novaic-cortex`.
- Run `python3 -m pytest -q` in `novaic-logicalfs`.
- Run sandbox-service pytest suite.
- Run final `rg` residue scans.

## Risks

- Old name strings may legitimately remain as guardrail forbidden patterns; check must classify them explicitly.

## Assumptions

- Historical roadmap references may remain if explicitly marked historical.
