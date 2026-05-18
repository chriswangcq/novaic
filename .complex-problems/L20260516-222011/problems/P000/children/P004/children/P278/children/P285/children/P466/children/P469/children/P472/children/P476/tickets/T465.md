# React saga config wiring ticket

## Problem Definition

The explicit `ReactSagaDecisionConfig` model exists, but `react_think.py` and `react_actions.py` still read `ServiceConfig` directly inside decision adapter functions. P476 must wire the config provider in without changing saga registration semantics.

## Proposed Solution

Add tiny overridable config accessors in the saga adapter modules, defaulting to `default_react_saga_decision_config()`. Use the returned config values when building `ReactThinkDecisionInput` and `decide_finalize_or_continue` inputs. Keep the accessors simple so tests can monkeypatch the accessor or pass deterministic config without touching global `ServiceConfig`.

## Acceptance Criteria

- `react_think._decide_and_build_actions` does not reference `ServiceConfig`.
- `react_actions._decide_finalize_or_continue` does not reference `ServiceConfig`.
- Both functions use `ReactSagaDecisionConfig` values.
- Saga definitions still register and compile.
- No broad compatibility fallback or duplicate config branch is added.

## Verification Plan

Run py_compile for changed saga modules and source guards for direct `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE` inside the decision adapter functions. Behavioral tests are handled by P477.

## Risks

- A provider accessor that is too magical could become another hidden global.
- Removing `ServiceConfig` imports may break tests that monkeypatch the old module import; P477 must update those tests.

## Assumptions

- A default provider at the saga adapter boundary is acceptable; the decision function should not directly read process config.
