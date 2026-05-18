# Imperative Dispatch Cleanup Final Verification

## Problem Definition

P483 needs a final, skeptical verification pass after P480/P481/P482. The risk is that new FSM/outbox code exists but production paths may still retain unclassified imperative dispatch, direct side-effect bypasses, stale fallback branches, or finalize/session compatibility residue.

## Proposed Solution

Run a focused verification sweep over runtime and queue/session production code, classify every guard hit, remove or tighten any high-confidence stale production residue, and rerun the focused runtime/session/FSM/outbox test set. Save both raw guard output and a classification matrix so the parent problem can be checked from concrete evidence rather than memory.

## Acceptance Criteria

- Broad guard searches are saved for direct saga creation, direct queue publish, legacy/fallback/compat dispatch names, active-session pointer residue, attach generation bypasses, and finalize/session-ended compatibility branches.
- Every production hit is classified as a required boundary, an intended FSM/outbox path, removable stale residue, or ambiguous follow-up candidate.
- Test and documentation guard fixtures are separated from production hits.
- Any high-confidence stale production residue is removed or tightened.
- Any ambiguous production hit is converted into a follow-up problem before P483 is allowed to succeed.
- Focused runtime/session/FSM/outbox tests pass.

## Verification Plan

Run guard commands from the repo root and save their raw output. Produce a short classification matrix with file/path evidence. Run the focused runtime test set covering session dispatch, outbox effects, generation-checked attach, finalize ownership, recovery, and direct side-effect guards. Compare the final diff and explicitly explain whether source changes were required.

## Risks

- Guard terms may overmatch tests and documentation; classification must not treat those as production residue.
- A required adapter boundary may look like a direct publish; verify call direction before deleting it.
- The repo has existing dirty changes, so only modify files needed for this ticket.

## Assumptions

- P480/P481/P482 cleanup children have already completed and their artifacts are available.
- `novaic-agent-runtime` is the primary production surface for this verification.
- Existing test guard files may intentionally contain retired strings to prevent regressions.
