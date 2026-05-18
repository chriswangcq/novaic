# Cortex handler and bridge residue classification check

## Summary

`P414` is successful. Cortex handler/bridge session identity uses explicit positive session-generation validation; remaining numeric defaults are Cortex/round/counter metadata.

## Evidence

- `R394` records the targeted guard and classification.
- Runtime focused tests passed: `20 passed in 0.31s`.
- Cortex focused tests passed: `20 passed in 0.37s`.

## Criteria Map

- Inspect Cortex handler and bridge hits: satisfied.
- Confirm session generation is explicit at archive/scope-end boundaries: satisfied by `require_positive_session_generation` and `require_positive_session_generation_value`.
- Classify `round_num` and counters: satisfied by `R394`.
- Patch dangerous fallback: none found.
- Run focused tests: satisfied.

## Execution Map

- `T401` executed as a two-file one-go classification.
- Initial combined command had wrong root paths for guard; execution reran root-level guard and separate Cortex tests before recording `R394`.

## Stress Test

- The corrected guard confirms the result was not based on an empty false-positive path run.

## Residual Risk

- None for P414.

## Result IDs

- `R394`
