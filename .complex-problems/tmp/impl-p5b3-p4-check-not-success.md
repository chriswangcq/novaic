# Phase 5B3.4 Compatibility Gate Check

## Summary

Not successful. Result `R049` found a real remaining compatibility-style surface: `include_display` still flows through runtime step-result formatting into Cortex as a boolean projection selector. The explicit projection contract is not fully clean until that adapter is removed.

## Blocking Gaps

- `StepFormattedRequest` still accepts `include_display`.
- `steps_read_formatted` still has an unknown/empty projection branch that selects display/history through `include_display`.
- `CortexBridge.read_step_formatted` and `step_result_client` still accept/pass `include_display`.
- Runtime tests still assert `include_display` payload values, proving the old boolean selector remains part of the contract.

## Result IDs

- R049
