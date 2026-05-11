# stale artifact namespace fixture check

## Summary

P007 is solved by R005. The stale `device-screenshot` namespace was removed from CLI/tool-output contract tests and replaced with `runtime-artifact`.

## Evidence

- `rg -n "device-screenshot" novaic-cortex/tests novaic-agent-runtime/tests/unit/task_queue` produced no matches.
- Affected Cortex tests passed.
- Affected runtime tests passed.

## Criteria Map

- Runtime-generated artifact fixtures use `runtime-artifact`: satisfied by patch.
- No `device-screenshot` remains in contract tests: satisfied by rg scan.
- Changes scoped to contract tests: only the two projection/tool-output fixture files changed.
- Relevant tests pass: satisfied.

## Execution Map

- R005 performed fixture cleanup and verification.

## Stress Test

- The exact stale string was searched across both affected test trees after patching, so hidden local occurrences in those contract tests are unlikely.

## Residual Risk

- Other non-CLI storage tests may still contain synthetic Blob refs such as `blob://payload/1`; those are not runtime artifact contract examples and are evaluated in final verification.

## Result IDs

- R005
