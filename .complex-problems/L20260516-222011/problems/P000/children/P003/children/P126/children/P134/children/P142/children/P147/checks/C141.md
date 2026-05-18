# step index metadata success check

## Summary

Success. `R127` closes the step-index child: compact metadata is present, artifact markers cover top-level and observation artifacts, zero durations are retained, and corrupt index rows now fail loudly instead of disappearing.

## Evidence

- Index row construction: `novaic-cortex/novaic_cortex/workspace.py:756-783`.
- Index row reader: `novaic-cortex/novaic_cortex/workspace.py:794-812`.
- Existing metadata coverage: `test_write_step_appends_to_index` checks tool/status/ts/duration/step_ref/has_artifacts/file.
- Added zero-duration and observation-artifact coverage: `test_index_keeps_zero_duration_and_observation_artifacts`.
- Added corrupt JSONL coverage: `test_read_step_index_rejects_corrupt_jsonl`.
- Verification run: `36 passed in 0.46s`.

## Criteria Map

- `write_step` and `read_step_index` source pointers: satisfied.
- `step_ref`, `payload_ref`, tool/status/duration metadata: satisfied by existing and retained tests.
- Artifact marker: satisfied for top-level artifacts and newly for `observation.artifacts`.
- Silent corruption: fixed by raising `ValueError` and covered by a regression test.

## Execution Map

- Result `R127` found three real edge issues: falsey duration omission, observation artifact omission, and corrupt-index swallowing.
- The patch corrected all three in the workspace boundary and added focused tests.

## Stress Test

- Tests include a zero-duration tool call, an artifact stored under the observation percept, and a mixed valid/corrupt `_index.jsonl` file. These target plausible history-navigation failures rather than only happy-path writes.

## Residual Risk

- Non-blocking for `P147`: active projection call-site completeness is still not judged here and remains under `P148`.

## Result IDs

- `R127`
