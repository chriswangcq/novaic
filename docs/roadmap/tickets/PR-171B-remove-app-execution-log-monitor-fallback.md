# PR-171B — Remove App Execution-log User Monitor Fallback

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Parent | [PR-171](PR-171-final-old-path-physical-deletion.md) |
| Repos | novaic-app |
| Theme | Old UI path deletion |

## Current-State Analysis

The normal Agent Monitor has moved to Cortex Activity Timeline. The App still physically carried the old execution-log component tree, old hook, old store export, and old view option names, creating a misleading user/debug hybrid path.

## Plan

- Delete the old execution-log monitor component tree and hook/store utilities.
- Rename user-facing monitor option to Agent Monitor.
- Remove the `execution-logs` App entity contract exposure.
- Keep only Activity Timeline as the normal ChatPanel monitor source.

## Verification Required

- [x] App unit tests for ChatPanel Activity Timeline guard and ActivityTimeline rendering.
- [x] Entangled contract test proving App no longer exposes `execution-logs`.
- [x] Full App unit test suite.
- [x] App build.
- [x] Frontend deployment.
- [x] GitHub commit for `novaic-app` and parent submodule pointer.

## Closure Evidence

- Physically deleted the old execution-log monitor component tree, `useLogs`, log view model, App execution-log entity contract, and old log formatter utilities.
- `cd novaic-app && npm run test:unit -- src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/components/Visual/ActivityTimeline.guard.test.ts src/components/Visual/ActivityTimeline.test.tsx src/components/hooks/useActivityTimeline.test.ts src/data/entities/entangledEntityContracts.test.ts` → 12 passed.
- `cd novaic-app && npm run build && npm run test:unit` → build passed; 37 tests passed.
