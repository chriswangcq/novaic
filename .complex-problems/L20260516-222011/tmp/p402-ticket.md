# Guard inventory execution ticket

## Problem Definition

Create a concrete compatibility-residue guard inventory across runtime, Cortex, tests, and migration-like files so cleanup children can act on file evidence rather than intuition.

## Proposed Solution

Run a read-only set of broad and narrow `rg` guards over:

- `novaic-agent-runtime/queue_service`
- `novaic-agent-runtime/task_queue`
- `novaic-agent-runtime/tests`
- `novaic-cortex/novaic_cortex`
- `novaic-cortex/tests`
- any migration-like files found under the relevant repos

Capture guard outputs into ledger tmp files, then summarize hits into a matrix with initial classifications: safe validator/test, harmless counter/projection, dangerous live compatibility, or cleanup-needed ambiguity.

## Acceptance Criteria

- Guard output files are saved under the ledger tmp directory.
- The inventory includes runtime, Cortex, tests, and migration-like scopes.
- Every non-empty guard group has an initial classification and evidence pointer.
- The result identifies which child problems should inspect the hits.
- No implementation code is modified in this inventory ticket.

## Verification Plan

- Use `rg` guards for generation/session_generation/finalize_generation/expected_generation/current_generation plus `or 0`, `or 1`, `None`, `current_active`, active clear/restart/archive helpers, and compatibility naming.
- Use `git diff --stat` before/after if needed to confirm no implementation edits came from the inventory ticket.
- Record exact commands or guard file paths in the result.

## Risks

- Guards may produce false positives; classification must preserve them as explicit evidence.
- A too-narrow regex could miss compatibility residue, so include both narrow live-session and broad suspicious searches.

## Assumptions

- This ticket is read-only except for ledger evidence files.
- Cleanup and tests belong to downstream children, not this inventory.
