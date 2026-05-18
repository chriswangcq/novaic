# Task queue production hits classified

## Summary

Classified all P531 production residue hits under `novaic-agent-runtime/task_queue`. The scan found 45 hits across 14 production files. Most hits are current explicit contracts (`remaining_stack` finalize payloads, worker publish adapters, artifact manifest shaping, and docstring-only optional wording). One risky residue was identified: `SagaStep.optional` / `add_*_step(optional=...)` appears to be stale unimplemented substrate semantics, and `wake_finalize.py` still passes `optional=True`.

## Done

- Filtered P531 production scan output to task_queue production paths.
- Recorded total task_queue production hits and unique file counts.
- Built context slices around every hit for review.
- Classified all 14 production files by category and rationale.
- Identified follow-up-worthy residue in saga optional-step semantics.

## Verification

- Count reconciliation:
  - `task-queue-production-hits.txt` has 45 lines.
  - `task-queue-production-counts.txt` reports 14 unique files.
  - The classification table has exactly 14 file rows.
- Stress check:
  - `remaining_stack` hits were traced through ReactThink/ReactActions, wake_finalize, Cortex/session handlers, client bridge, and client API. They are current explicit finalize state, not legacy compatibility residue.
  - `publish` hits were traced to TaskQueue client and worker effect interpreters. They are side-effect adapters, not pure-FSM bypasses.
  - `optional` hits were separated into harmless docstrings, artifact manifest shaping, and the risky saga substrate field. The saga substrate field is follow-up-worthy because active DAG construction/execution does not consume it.

## Known Gaps

- The risky `optional` saga-step residue is classified but not fixed in this result. It should become a follow-up problem so the code can either delete the stale field/call site or intentionally implement optional-step semantics.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-hits.txt`
- `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-counts.txt`
- `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-context.txt`
- `.complex-problems/L20260516-222011/tmp/p538/task-queue-production-classification.md`
