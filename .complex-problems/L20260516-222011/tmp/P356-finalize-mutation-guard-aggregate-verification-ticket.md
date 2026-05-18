# Aggregate finalize mutation guard verification

## Problem Definition

P356 must prove that the P350 finalize mutation hardening work is correct as a composed runtime path, not only as isolated fixes. The verification must cover Cortex scope-end mutation guards, terminal subagent status mutation guards, wake-finalize payload propagation, and session finalize ownership behavior.

## Proposed Solution

Run an aggregate verification pass over the P350-owned runtime paths. The pass will combine focused test execution, source residue searches, and direct code inspection around finalize mutation entry points. The result must explicitly map each P350/P356 success criterion to evidence and must treat any missing evidence or stale compatibility branch as a follow-up problem instead of a tolerated gap.

## Acceptance Criteria

- Focused tests cover Cortex scope-end, subagent terminal status mutation, wake-finalize payload builders, wake-finalize DAG gating, and session finalize ownership rejection behavior.
- Source searches show no live `last_scope_id` or `last_scope_archived_at` propagation in finalize mutation payloads.
- Source searches show no missing-generation compatibility fallback such as generation defaulting to zero in the touched runtime paths.
- Direct inspection identifies every Business/status mutation path relevant to finalize and confirms each path is guarded by explicit scope identity and positive session generation where required.
- Every P356 success criterion is mapped to concrete command output or file evidence.
- Any remaining uncertainty is recorded as a follow-up, not hidden in the aggregate result.

## Verification Plan

Run `py_compile` for touched finalize/session/subagent/FSM modules, execute the focused pytest suite used by P353/P354/P355, perform residue searches with `rg`, and inspect the small set of finalize mutation files directly. Record command summaries, evidence pointers, and residual risk in the ticket result.

## Risks

- Aggregate tests may pass while a rarely used handler still accepts stale payload shape; mitigate with source searches and direct mutation-path inspection.
- Existing dirty worktree may contain unrelated changes; mitigate by scoping inspection to P350-owned runtime paths and not reverting unrelated files.
- A too-broad search can produce historical ledger/docs noise; mitigate by searching production/test runtime paths separately from `.complex-problems`.

## Assumptions

- P353, P354, and P355 results are available as prior evidence, but P356 must still rerun aggregate checks rather than relying only on summaries.
- Recovery compensation hazards outside finalize mutation ownership remain under sibling work and are not silently claimed solved by this aggregate pass.
