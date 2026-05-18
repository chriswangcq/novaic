# Check: P427 projection and guard verification

## Verdict

Success.

## Evidence Reviewed

- Result `R406`
- Focused pytest artifact with `90 passed`.
- Projection guard artifact.
- Formatter slices showing display gating.

## Criteria Map

- Focused tests pass: satisfied, `90 passed in 0.49s`.
- No `stable_json(observation)` fallback: satisfied, guard has no hits.
- `include_display=True` display-perception only: satisfied, guard shows history/current use `False`, display perception uses `True`.
- Any regression candidate fixed/split: no candidate found.

## Execution Map

The execution ran both behavioral tests and source-level guards. It did not rely on prior success checks alone.

## Stress Test

I checked for the exact prior failure class: unknown tool observations or display/base64 shaped payloads being projected into history/current messages. The previous fallback is absent and formatter gating is explicit.

## Residual Risk

None inside P427. This proves the current ContextEvent projection path and focused guards; P428 still performs broader residue search.
