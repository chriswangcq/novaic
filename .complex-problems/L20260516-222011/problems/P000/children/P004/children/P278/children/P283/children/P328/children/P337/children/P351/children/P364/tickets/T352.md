# Recovery compensation finalize aggregate verification

## Problem Definition

P364 must verify P351 as a composed recovery/compensation finalize system after P361 source mapping, P362 compensation hardening, and P363 recovery archive hardening. The check must prove there is no remaining recovery or compensation path that can synthesize ambiguous finalize mutation work.

## Proposed Solution

Run focused tests and residue searches across the Queue Service recovery/compensation surface. Inspect the remaining `wake_finalize`, `session_generation`, recovery archive, and saga compensation references and map each P351 criterion to concrete evidence. Record any remaining uncertainty as a follow-up.

## Acceptance Criteria

- Focused tests cover compensation generation preservation, invalid compensation suppression, recovery marker/effect generation preservation, invalid recovery archive rejection, and direct session finalize ownership.
- Source searches under `queue_service` do not reveal generation defaulting in recovery/compensation-created finalize mutation paths.
- Every P351 success criterion is mapped to evidence from child results and aggregate commands.
- Any remaining recovery/compensation identity gap becomes a follow-up rather than being hidden.

## Verification Plan

Run `py_compile` for touched queue-service modules, run the focused recovery/compensation/finalize pytest suite, run `rg` residue searches for `wake_finalize`, `session_generation`, `finalize_generation`, `generation or 0`, and direct `CORTEX_SCOPE_END` recovery archive publication, then record the evidence.

## Risks

- Searches may include generic FSM ledger generation fields that are not session finalize identity; the result must distinguish benign queue FSM generation from recovery/finalize session generation.
- Existing unrelated worktree changes may appear in diffs; keep the aggregate check scoped to P351-owned paths.

## Assumptions

- P361/P362/P363 checks are trusted child evidence but aggregate commands must still be rerun.
