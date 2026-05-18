# Compatibility residue guard audit ticket

## Problem Definition

The generation boundary has been tightened in multiple focused areas, but the repository still needs a dedicated compatibility-residue audit for optional generation branches, default generation values, legacy tests, migrations, outbox workers, and saga/runtime handlers. The goal is to prove that attach/finalize/session-ended paths cannot silently accept missing or stale generation through leftover compatibility code.

## Proposed Solution

Run a skeptical source-guard and test audit in bounded stages:

1. Build a guard inventory across `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, `novaic-agent-runtime/tests`, `novaic-cortex/novaic_cortex`, and relevant migration/test directories for:
   - `generation` / `session_generation` defaulting to `0`, `1`, current active state, or `None`.
   - optional generation branches that treat missing generation as valid.
   - compatibility tests that assert missing/stale generation succeeds.
   - direct active-session clear/restart/archive paths that do not require explicit generation.
2. Classify every hit as:
   - required explicit validator or test coverage,
   - harmless diagnostic/projection/counter,
   - dangerous compatibility residue,
   - ambiguous and requiring a child problem.
3. Remove dangerous residue instead of preserving backward compatibility.
4. Add focused tests for every removed/changed live path.
5. Rerun the guard matrix and focused tests until no unclassified residue remains.

If the inventory spans multiple independent surfaces, split into child problems for source guard inventory, runtime compatibility cleanup, Cortex compatibility cleanup, test/migration cleanup, and final aggregate verification.

## Acceptance Criteria

- A guard matrix exists for optional/missing/stale generation compatibility residue across runtime queue, task handlers, Cortex code, tests, and migration-like files.
- Every guard hit is classified with file evidence.
- Dangerous compatibility residue is removed or moved into a child fix ticket.
- Attach/finalize/session-ended paths fail closed for missing, stale, bool, malformed, or implicitly looked-up generation.
- Focused tests and source guards prove no unclassified live compatibility path remains.

## Verification Plan

- Use `rg` guards over runtime, Cortex, tests, and migrations for `generation`, `session_generation`, `expected_generation`, `finalize_generation`, `current_generation`, `or 0`, `or 1`, `None`, `current_active`, and active clear/restart/archive helpers.
- Run focused runtime tests covering attach/finalize/session-ended/recovery/outbox/session FSM.
- Run focused Cortex tests covering context-event lifecycle, scope archive diagnostics, and operational-store generation boundaries if Cortex hits appear.
- Rerun final narrow and widened guard matrices and record all remaining hits as fixed or safe.

## Risks

- The guard surface is broad and likely includes many harmless counters or tests; classification must not become hand-wavy.
- Some tests may encode legacy behavior and require deletion/rewrite, not expansion.
- This ticket may be too broad for one-go; split if multiple live surfaces appear.

## Assumptions

- No backward compatibility is required for unsafe missing/stale generation behavior.
- Code deletion is preferred over compatibility shims when a path is no longer required.
- Existing closed children under `P328` can be cited, but this ticket must still run its own residue audit rather than assuming prior work found everything.
