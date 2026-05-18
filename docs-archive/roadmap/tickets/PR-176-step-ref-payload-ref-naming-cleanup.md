# PR-176 — Step Ref / Payload Ref Naming Cleanup

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-cortex`, `novaic-agent-runtime`, docs |
| Depends on | PR-171 |
| Theme | Naming entropy cleanup |

## Goal

Replace product-facing and active Runtime/Cortex join-key naming that still says `result_id` with clearer `step_ref` / `payload_ref` semantics.

## Current-State Analysis

`payload_ref` is the correct raw payload locator. Some active Cortex/Runtime
internals still use `result_id` as the step/payload join key, which is easy to
confuse with retired result-store or execution-log terminology.

## Implementation

- Use `step_ref` as the canonical tool-step join key in Runtime context messages and Cortex read APIs.
- Use `payload_ref` for raw payload lookup.
- Remove active `result_id` naming where it is not an archived test/history artifact.
- Update tests and documentation.

## Tests / Smoke

- Runtime tool-result expansion tests use `step_ref`.
- Cortex step read/project tests use `step_ref` and hide it from Activity Timeline.
- Guard grep prevents active `result_id` product leakage.

## Closure

- Runtime tool execution now returns `step_ref`.
- Runtime save-results and Cortex step read/project APIs use `step_ref`; `payload_ref` remains the payload locator.
- Active code grep for `result_id` / `step-result` is clean except App guard tests that explicitly ban `result_id`.
- Tests passed:
  - `novaic-common`: `PYTHONPATH=.:../novaic-agent-runtime pytest -q`
  - `novaic-cortex`: `PYTHONPATH=.:../novaic-common pytest -q`
  - `novaic-agent-runtime`: `PYTHONPATH=.:../novaic-common pytest -q`
  - `novaic-app`: `npm run test:unit -- ActivityTimeline useActivityTimeline entangledEntityContracts`

## Deploy / GitHub

- Deploy services after tests pass.
- Commit and push touched repos plus parent submodule pointers.
