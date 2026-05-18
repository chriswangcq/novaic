# PR-186D — App Agent Monitor Public-Surface Acceptance

Status: `[closed]` — 2026-05-03

## Analysis

The App default Agent Monitor uses Activity Timeline records and already hides raw diagnostic fields. Message status remains delivery UI, not the agent loop driver.

The gap is an acceptance guard that the normal monitor is a user-facing "agent is working" surface, not a developer execution-log viewer.

## Scope

- Add or tighten App tests for Observation / Reasoning / Action / Summary rendering.
- Guard that `result_id`, raw MCP content, HTTP bodies, stack traces, and execution-log fallback do not render in the normal monitor.
- Keep developer diagnostics separate if reintroduced later.

## Tests

- App targeted unit tests for Activity Timeline.
- App full unit tests and build before closure.

## Deployment / Git

- If only tests/docs change: no frontend deploy required.
- If UI behavior changes: deploy frontend and record smoke evidence.

## Closure

- Added `src/components/Visual/ActivityTimeline.acceptance.test.tsx`.
- Covered Observation / Reasoning / Action / Summary rendering and absence of normal-monitor debug vocabulary.
- Tests:
  - `npm run test:unit -- ActivityTimeline.acceptance.test.tsx` → `1 passed`
  - `npm run test:unit` → `38 passed`
  - `npm run build` → passed
- No frontend deploy required; no behavior changed.
