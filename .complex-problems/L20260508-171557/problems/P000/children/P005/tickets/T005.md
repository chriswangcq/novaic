# T005 Scheduler And Health Action Specs

## Problem Definition

Scheduler and health engines already use `EffectPlanRunner`, but action payload construction and result classification still live directly inside the engines. This keeps business outcome classification mixed with protocol timing and metrics updates.

## Proposed Solution

- Add scheduler action spec helpers for:
  - due-agent scan effect
  - scheduled wake dispatch effect
  - dispatch result classification
  - dispatch error classification
- Add health action spec helpers for:
  - recover-all effect
  - recovery response normalization
- Update scheduler and health engines to consume those helpers while keeping metrics/logging in the engine.
- Add pure tests for scheduler classifications and health recovery specs.

## Verification Plan

- Run new scheduler/health action spec tests.
- Run existing scheduler/health dispatch and generic worker tests.
- Run effect-boundary and runtime supervision lint checks.

## Acceptance Criteria

- Scheduler dispatch outcomes are represented by explicit classifications.
- Health recovery effect/result payloads are represented by explicit helpers.
- Engines continue to use `EffectPlanRunner` and do not contain direct effect helper residue.
- Existing scheduler/health behavior remains green.
