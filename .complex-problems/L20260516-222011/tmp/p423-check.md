# Check P423 against R403

## Verdict

success

## Skeptical Review

P423 was a one_go audit, so I checked for actual enforcement points, not just tests. The inspected code has hard failures for inline `result`, missing observation, missing payload ref, and missing Blob client for large payloads.

## Criteria Review

- `write_payload`, `read_payload`, `normalize_step`, and `write_step` inspected: satisfied.
- Tool steps reject inline `result`: satisfied and covered by `test_write_step_rejects_inline_tool_result`.
- Tool payloads require `payload_ref`: satisfied in `normalize_step` and `write_payload`.
- Externalized payload manifests stay pointer-oriented: satisfied by manifest fields and external Blob ref tests.
- Focused tests pass: satisfied by `55 passed`.

## Stress Test

The check included the dangerous paths: inline result, missing observation, large payload without Blob service, externalized payload readback, corrupt/missing payload records, and payload ref mismatch.

## Residual Risk

No workspace step/payload normalization risk remains in P423. Archive and API lifecycle work are separate child problems.

## Evidence

- `.complex-problems/L20260516-222011/tmp/p423/workspace-step-payload.inspect.txt`
- `.complex-problems/L20260516-222011/tmp/p423/workspace-step-payload-guard.txt`
- Focused pytest: `55 passed in 0.47s`.
