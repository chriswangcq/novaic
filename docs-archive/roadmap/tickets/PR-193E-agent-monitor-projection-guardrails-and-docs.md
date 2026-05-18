# PR-193E — Agent Monitor Projection Guardrails and Docs

Status: closed

## Analyze

Several docs still describe Cortex Activity Timeline as a direct product path. Those docs were accurate for PR-169/188, but are now misleading after the Entangled projection cutover.

## Small Work Orders

1. Update architecture docs to state: Agent Monitor is an Entangled product projection.
2. Keep Cortex as working-trace source of truth, not App read API.
3. Document that large/debug payloads remain outside the normal monitor.
4. Add guard tests so docs/code do not reintroduce:
   - `agents.activity_timeline`
   - `execution-logs` monitor source
   - raw `subagents` App subscription
   - polling in `useActivityTimeline`

## Tests

- App guard tests.
- Business guard tests.
- Common contract tests.

## Acceptance

Docs and guardrails describe the same one-path architecture that code enforces.

## Closure

Closed 2026-05-03. Current architecture docs describe Agent Monitor as an Entangled product projection; static guards cover App, Business, Common, and Cortex old-path reintroduction.
