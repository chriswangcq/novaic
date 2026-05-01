# PR-154A — Remove App Log Payload Diagnostic Path

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-154 |
| Repos | novaic-app, docs |

## Goal

Physically remove the unused App-side execution-log payload fetch/cache path so the normal Agent Monitor cannot grow back into a raw diagnostic payload viewer.

## Why This Matters

The product surface is "agent monitor", not "developer execution payload inspector". The UI already renders semantic summaries; keeping an unused lazy payload cache and `log-payloads.get_payload` client path creates maintenance entropy and a future footgun.

## Implementation Plan

1. [x] Remove `logInputCacheStore` and related imports.
2. [x] Remove `fetchLogInput`, `logInputCache`, and payload-aware `entityToLogVM` wiring from `useLogs`.
3. [x] Remove the unused `log-payloads` App entity contract export.
4. [x] Remove unused technical/result helper exports and tests that only preserve diagnostic payload behavior.
5. [x] Keep semantic display contract tests and monitor component tests.

## Unit / Guardrail Tests

- [x] `ExecutionLog` component tests prove raw ids/payload labels remain hidden.
- [x] `executionLogUtils` tests prove semantic display kinds match Common contract.
- [x] App unit tests/build pass.

## Smoke / Deploy / Git

- [x] Build App.
- [x] Deploy frontend OTA if App changed.
- [ ] Commit App.
- [ ] Parent repo submodule/docs commit and push.

## Evidence

- `npm run test:unit -- --run src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx src/components/hooks/useLogs.test.ts src/data/entities/entangledEntityContracts.test.ts` — 15 passed.
- `npm run build` — passed.
- `./deploy frontend` — deployed frontend v0.3.0 to `https://relay.gradievo.com/resource/frontend/v0.3.0/`.
- Guard search for removed App payload cache/diagnostic exports returned no matches under `src/`.
