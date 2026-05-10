# P035 success check

## Summary

Success. R028 closes P035: tool step normalization now has an explicit reusable boundary, returns the final durable payload reference before event emission, preserves existing validation behavior, and avoids hidden caller mutation.

## Evidence

- R028 changed `novaic-cortex/novaic_cortex/workspace.py` to add `Workspace.normalize_step(scope_path, step)`.
- R028 changed `Workspace.write_step` to consume the normalized copy.
- R028 added/updated tests in `novaic-cortex/tests/test_step_index_outcome.py`.
- Targeted verification passed: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_step_index_outcome.py tests/test_workspace.py -q` → `23 passed`.
- Full verification passed: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `443 passed`.

## Criteria Map

- Reusable normalization path: met by `Workspace.normalize_step`.
- Final `payload_ref` before event append: met because `normalize_step` externalizes inline payloads and returns the resulting `payload_ref`.
- Existing validation rules intact: met because previous validation moved into `normalize_step` and the existing validation tests still pass.
- Focused tests cover payload and non-payload steps: met through the new mutation/payload tests plus existing step index and workspace tests.

## Execution Map

- P035 ticket T031 executed in R028.
- Implementation stayed within the intended Workspace boundary.
- P036 remains responsible for wiring `/v1/steps/write` to `ToolStepRecorded`; this check does not claim that cutover is complete.

## Stress Test

- Checked mutation safety by asserting the original input retains inline `payload`, unmodified `observation`, and no injected `seq` after `write_step`.
- Checked payload durability by reading the externalized payload back from the payload store.
- Ran the full Cortex suite to catch regressions in archival, payload inspection, projections, API contracts, and legacy step reads.

## Residual Risk

- Normalization intentionally writes payloads before step/event writes, matching the previous legacy ordering. A later transaction/outbox ticket can make that stronger, but it is not a blocker for this phase.
- No remaining P035-specific blocker.

## Result IDs

- R028
