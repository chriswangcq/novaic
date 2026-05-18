# Run final projection static branch audit

## Problem Definition

After cleanup, active code still needs a static sweep for projection/media/base64/fallback residues. Findings must be classified so remaining branches are intentional rather than accidental.

## Proposed Solution

Run targeted `rg` searches across active Cortex/runtime/factory production and tests, inspect suspicious matches, and classify them as intentional, already removed, or requiring follow-up.

## Acceptance Criteria

- No active `resolve_for_llm` references remain.
- Projection/media/base64 branches in active code are classified.
- Suspicious unclassified findings become follow-up work.

## Verification Plan

Run targeted `rg` commands and inspect active-code matches around suspicious projection branches.

## Risks

- Static search may produce many docs/ledger hits; focus on active production/test files.

## Assumptions

- Docs/ledger mentions are not active runtime residue unless they point to stale implementation instructions.
