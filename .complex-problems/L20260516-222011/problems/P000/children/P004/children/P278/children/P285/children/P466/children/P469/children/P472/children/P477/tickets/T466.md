# React saga config tests ticket

## Problem Definition

The react saga config model and wiring are present, but behavior must prove that config is explicit. Existing tests still include a monkeypatch of `react_actions.ServiceConfig`, which should be replaced because that import was removed.

## Proposed Solution

Update focused tests to pass `ReactSagaDecisionConfig` directly into the decision adapter functions. Add a react-think test that uses non-default stack-hold/round values. Add a source guard ensuring decision adapter functions no longer directly reference `ServiceConfig`.

## Acceptance Criteria

- `test_round_cap_still_forces_finalize` no longer monkeypatches global `ServiceConfig`.
- At least one `react_think` adapter test passes explicit `ReactSagaDecisionConfig` and verifies deterministic routing.
- A guard test or saved guard artifact proves direct `ServiceConfig` references are absent from decision adapter function bodies.
- Focused tests pass and logs are saved under `.complex-problems/L20260516-222011/tmp/p477/`.

## Verification Plan

Run focused pytest files that cover turn finalization and runtime explicit contracts. Run an explicit source guard command over `react_think.py` and `react_actions.py`.

## Risks

- Tests may import private adapter functions, but these tests already use private saga adapters as contract guards.
- A source guard that scans too broadly may flag the intended provider boundary; slice function bodies instead.

## Assumptions

- Behavioral tests can pass optional config args added by P476.
