# Saga decision config injection ticket

## Problem Definition

Saga routing adapters currently read round/stack limits from `ServiceConfig` while building decision inputs. The pure decision functions already accept explicit values, so the remaining problem is the adapter boundary: tests should be able to vary these limits without monkeypatching global config.

## Proposed Solution

Introduce a small explicit config snapshot/provider for react saga limits and thread it through the `react_think` and `react_actions` adapter functions. Keep process-level `ServiceConfig` reads at the assembly/default-provider boundary. Update focused tests to pass explicit config values and prove behavior changes deterministically.

## Acceptance Criteria

- `react_think._decide_and_build_actions` and `react_actions._decide_finalize_or_continue` no longer directly reference `ServiceConfig`.
- A clear explicit config type/provider owns `max_rounds_before_force_finalize` and `max_stack_hold_retries` values.
- Focused tests can pass non-default limits without monkeypatching `ServiceConfig`.
- Existing saga behavior remains compatible with default config.

## Verification Plan

Run targeted unit tests for react think/actions decision routing and any session finalizer tests touched by the refactor. Run a guard ensuring direct `ServiceConfig.MAX_ROUNDS_BEFORE_FORCE_FINALIZE` reads are absent from these decision adapter functions.

## Risks

- Saga definitions may rely on module-level callback signatures, so the injection point must fit existing callback plumbing.
- A too-broad refactor could disturb saga registration.

## Assumptions

- It is acceptable to keep `ServiceConfig` reads in a default provider if the provider is explicitly passed/overridable.
