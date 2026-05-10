# Remove include_display From Step Formatting Projection API Check

## Summary

Success. Result `R050` removed the boolean `include_display` selector from the step formatting API path and verified that runtime/Cortex now use explicit projection only.

## Evidence

- `StepFormattedRequest` no longer has `include_display`.
- `/v1/steps/read_formatted` now accepts explicit projections and rejects unsupported values with HTTP 400.
- `CortexBridge.read_step_formatted`, `expand_step_ref_to_content`, `fetch_step_for_llm`, and `expand_messages_for_llm` no longer accept or forward `include_display`.
- Static search over the relevant API/client/test files returned no `include_display` matches.
- Workspace search shows remaining `include_display` hits only in lower-level `step_result_projection` formatting/`resolve_for_llm` behavior and its test, which is outside the step formatting request/client path.
- Targeted Cortex and runtime tests passed, and compile checks passed.

## Criteria Map

- Remove `include_display` from Cortex request/client path: satisfied.
- Remove boolean projection branch: satisfied.
- Runtime tests assert projection-only payloads: satisfied.
- Static search leaves only unrelated byte-resolution behavior: satisfied.
- Targeted tests pass: satisfied.

## Execution Map

- The follow-up directly closed the blocker found by P055.
- It did not remove `include_display` from `resolve_for_llm`, because that function controls byte/image resolution behavior and is not the step formatting request compatibility surface.

## Stress Test

- The check includes both Cortex-side and runtime-side tests, so the endpoint and its only workspace callers were verified together.

## Residual Risk

- None for this follow-up.

## Result IDs

- R050
