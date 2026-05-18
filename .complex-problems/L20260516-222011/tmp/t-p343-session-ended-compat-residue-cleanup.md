# Session-ended compatibility residue cleanup

## Problem Definition

After P341/P342, the direct session-ended delivery path rejects zero generation, but compatibility residue may still exist in tests or upstream contracts that normalize missing `session_generation` to `0`. P343 must remove or explicitly classify those residues so the project does not keep misleading "zero is fine" code around.

## Proposed Solution

1. Search live code and tests for finalize/session-ended generation fallback patterns:
   - `session_generation: int = 0`
   - `ctx.get("session_generation") or 0`
   - tests that intentionally pass or assert finalize `session_generation=0`
   - delivery handler/client/route compatibility language.
2. Classify each match:
   - in P336 delivery boundary and must be deleted/fixed now.
   - upstream react contract and should be delegated to P337/P339 if still outside this ticket.
   - unrelated attach/runtime state and should not be touched.
3. Remove or rewrite P336 delivery-boundary compatibility residue.
4. Add/adjust tests or source guards that prevent the delivery boundary from reintroducing zero-generation compatibility.

## Acceptance Criteria

- No P336 session-ended delivery code silently fills missing generation with zero.
- No P336 delivery tests bless zero generation as valid.
- Remaining `session_generation=0` defaults are either removed or explicitly documented as P337/P339 upstream contract work.
- Source guard commands are recorded for P344 aggregate verification.

## Verification Plan

- Run targeted `rg` guards over `task_queue/sagas/wake_finalize.py`, `task_queue/handlers/session_handlers.py`, `task_queue/client.py`, `queue_service/routes.py`, and relevant tests.
- Run finalize ownership and legacy cleanup tests after any residue removal.
- If upstream react contracts must be changed to prevent P336 from being meaningful, spawn or split instead of hiding that scope expansion.

## Risks

- Over-broad search results can tempt unrelated cleanup. Keep P343 focused on P336 delivery residue and explicitly delegate broader contract work.
- If an existing test deliberately asserts `session_generation=0`, deleting it may require updating a deeper contract expectation.

## Assumptions

- Backward compatibility for zero-generation finalize/session-ended delivery is not required.
