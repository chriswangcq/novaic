# Finalize and session compatibility branch cleanup ticket

## Problem Definition

P482 must review finalize, session-ended, attach, and recovery paths for old compatibility/fallback branches after the FSM migration. These paths are sensitive because stale fallback behavior can hide dangling skills, missing generations, or direct session mutation outside explicit FSM decisions.

## Proposed Solution

Run targeted guards over finalize/session-ended/attach/recovery files for legacy, compat, fallback, missing-generation, stale-generation, previous/last scope, and direct mutation language. Classify retained hits as active FSM behavior, guard/test fixture, adapter boundary, high-confidence removable residue, or ambiguous. Remove/tighten high-confidence stale branches; spawn a smaller child if a branch is ambiguous. Run focused finalize/session runtime tests after any change.

## Acceptance Criteria

- Guard artifacts are saved with searched terms and matching files.
- Retained finalize/session compatibility hits are classified with file references.
- High-confidence stale branches are removed or tightened.
- Ambiguous branches are spawned into smaller child problems.
- Focused finalize/session tests pass after any source change.

## Verification Plan

Use targeted `rg` and file inspection across `queue_service/session_fsm.py`, `session_repo.py`, `session_rebuild.py`, `session_recovery.py`, `saga_repo.py`, runtime finalize handlers, and relevant tests. Run focused tests covering finalize ownership, session-ended enforcement, missing/stale generation handling, and session harness residue guards.

## Risks

- The words `missing_generation` and `fallback` may represent explicit FSM decisions or tests, not stale compatibility.
- Over-deleting recovery/finalize branches can break dead-session recovery.

## Assumptions

- Cleanup should be conservative but not hand-wave retained branches; ambiguous items must become smaller problems.
