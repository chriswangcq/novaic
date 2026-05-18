# ContextEvent read model success check

## Summary

Success. R122 satisfies the read-model success criteria and improved coverage by adding the missing empty-root-path regression test. Verification includes both focused read-model tests and the full ContextEvent store/projection/read-model bundle.

## Evidence

- Source pointers cover prepared context status, reset boundary, constructor dependencies, prepare flow, budget compaction, token counting, usage ratio, and top-first stack normalization.
- Production code shows no legacy fallback in `ContextEventReadModel.prepare`: non-empty missing streams raise `ContextEventReadModelResetRequired`.
- Added test covers empty root path closed/empty prepared context.
- Focused test result:

```text
4 passed in 0.09s
```

- ContextEvent bundle result:

```text
49 passed in 0.16s
```

## Criteria Map

- Read-model behavior for empty roots, projection, budget compaction, token counting, usage ratio, and top-first stack normalization is documented:
  - Satisfied by R122 `Done` section and new empty-root test.
- Read-model tests are identified and run:
  - Satisfied by R122 `Verification`; focused read-model tests and combined ContextEvent tests passed.
- Any implicit fallback to old context assembly is classified and fixed or split:
  - Satisfied. This layer does not read `context.jsonl`; non-empty missing event streams raise reset-required. Workspace materialized projection helpers are tracked separately under P134.

## Execution Map

- Inspected `novaic-cortex/novaic_cortex/context_event_read_model.py`.
- Inspected `novaic-cortex/tests/test_context_event_read_model.py`.
- Added `test_event_read_model_empty_root_path_returns_closed_empty_context`.
- Ran focused and combined ContextEvent test bundles.
- Recorded R122.

## Stress Test

- Plausible failure mode: empty root path returns malformed status or executing phase.
  - Covered by newly added empty-root test.
- Plausible failure mode: non-empty root with missing event stream silently falls back to old context files.
  - Covered by existing reset-required test and source mapping.
- Plausible failure mode: long tool output bypasses the budget boundary.
  - Covered by `test_event_read_model_applies_budget_compaction_to_projected_messages`.
- Plausible failure mode: stack order is reversed incorrectly for control/status.
  - Covered by read-model projection test that expects top/current wake first.

## Residual Risk

- Non-blocking: workspace `context.jsonl` projection helpers remain to be audited under P134.
- Non-blocking: runtime prepare-context handoff remains to be audited under P135.

## Result IDs

- R122
