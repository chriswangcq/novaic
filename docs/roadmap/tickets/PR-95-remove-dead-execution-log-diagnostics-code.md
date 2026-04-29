# PR-95 — Physically remove dead execution-log diagnostics UI code

| Field | Value |
| --- | --- |
| **Ticket** | PR-95 |
| **Status** | `[✓]` |
| **Scope** | `novaic-app` |
| **Depends on** | PR-94 |
| **Invariant** | The execution-log surface is an Agent Monitor. Dead developer-diagnostics UI code must not remain hidden behind a disabled flag. |

## Problem

PR-94 stopped rendering debug details in the user-facing execution-log expanded state, but the old diagnostics implementation still exists in `ExecutionLog.tsx` behind a hard-disabled flag. That keeps the component conceptually noisy and makes future regressions easier.

## Goal

Physically remove the old, unused diagnostics UI path from the App component:

- no hidden LLM input/debug modal path;
- no hidden raw JSON / `SmartValue` diagnostics blocks;
- no hidden TRS / Factory drilldown from the Agent Monitor row;
- no dead imports, helper types, helper components, or local state that only supported the removed diagnostics path.

## Non-Goals

- Do not remove Runtime / Entangled metadata fields such as `result_id` or `factory_log_id`.
- Do not remove the log payload cache or backend log-payload APIs.
- Do not introduce a new developer diagnostics panel.
- Do not change collapsed Agent Monitor semantics from PR-93/PR-94.

## Implementation Checklist

- [x] Remove unused LLM debug modal code from `ExecutionLog.tsx`.
- [x] Remove unused TRS/debug renderer helpers from `ExecutionLog.tsx`.
- [x] Remove `showDeveloperDiagnostics` and all hidden diagnostic branches.
- [x] Remove unused imports and local state from `LogCard`.
- [x] Keep expanded rows deterministic and monitor-only.
- [x] Remove stale `fetchLogInput` UI prop plumbing from Agent Monitor components.

## Unit / Component Tests

- [x] Component test: expanded think row still shows `思考摘要` and no Factory/debug labels.
- [x] Component test: expanded `chat_reply` still shows `回复内容` and no result/debug labels.
- [x] Component test: expanded `skill_end` still shows `上下文摘要` and no TRS/debug labels.
- [x] Component test: failed row still shows human failure summary and no diagnostic labels.

## Smoke Test

- [x] Build App successfully.
- [x] Deploy frontend OTA.
- [x] Frontend OTA URL returns HTTP 200.

## Deployment Checklist

- [x] `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx src/components/hooks/useLogs.test.ts`
- [x] `npm run build`
- [x] `./deploy frontend 0.3.0`
- [x] Frontend OTA URL returns HTTP 200.

## GitHub / Commit Checklist

- [x] Commit App changes.
- [x] Push subrepo branch.
- [x] Bump parent repo submodule pointer and commit.

## Rollback

Revert the App cleanup commit. PR-94 monitor display behavior should remain recoverable from the previous commit.
