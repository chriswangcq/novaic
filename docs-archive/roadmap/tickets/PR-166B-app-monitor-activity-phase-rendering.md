# PR-166B — App Monitor Activity Phase Rendering

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | `novaic-app`, docs |
| Depends on | PR-166A, PR-166C |
| Theme | Agent Monitor product surface |

## Goal

Make the App Agent Monitor present each realtime execution-log event as product-level agent activity, grouped into the same user-facing phases as the Cortex Activity Timeline: observation, reasoning, action, and summary.

This ticket does not reintroduce developer diagnostics. It keeps the current lightweight Entangled `execution-logs` realtime stream, but the visible monitor language should explain what the agent is doing rather than expose transport details.

## Current-State Analysis

1. The App monitor still renders `execution-logs` through `useLogs` and `ExecutionLog`.
2. Existing App tests already guard that raw ids, MCP payload labels, input parameters, execution-result labels, and technical detail panels do not show in the normal monitor.
3. `executionLogUtils.ts` maps backend semantic `display_kind` into a title and summary, but it does not yet expose an explicit observation/reasoning/action/summary phase.
4. The App can add phase labeling without switching the realtime data source yet; Cortex PR-166A already provides the stricter projection contract for future API-backed views.

## Small Work Items

1. Add a local App display phase contract for monitor events.
2. Map existing semantic display kinds into observation/reasoning/action/summary.
3. Render the phase as user-facing monitor language in collapsed and expanded log cards.
4. Add unit tests that guard phase mapping and ensure the monitor still hides debug identifiers.
5. Run App tests/build, deploy frontend, and record evidence.

## Implementation Checklist

- [x] `ExecutionLogDisplay` includes a phase and phase label.
- [x] `thinking` maps to reasoning.
- [x] `environment_observed`, `payload_inspected`, and `file_viewed` map to observation.
- [x] `context_saved` maps to summary.
- [x] Reply/tool/subagent/wait events map to action.
- [x] Log card renders the phase label without showing raw result ids or payload diagnostics.
- [x] Focused App unit tests pass.
- [x] App build passes.
- [x] Frontend deploy completed.
- [x] Git commits created for App and root docs/submodule bump.

## Verification Plan

```bash
cd novaic-app
npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx
npm run build
cd ..
./deploy frontend
./deploy status
```

## Done Criteria

- Agent Monitor makes the work phase legible to a normal user.
- Normal and expanded views remain product-level, not diagnostic.
- Tests fail if phase mapping or raw debug hiding regresses.
- Deployed code is pushed with the parent repo submodule bump.

## Evidence

- Focused App tests: `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx` → 15 passed.
- Full App tests: `npm run test:unit` → 44 passed.
- App build: `npm run build` passed with existing Vite warnings.
- Deploy: `./deploy frontend` uploaded frontend `v0.3.0` to `https://relay.gradievo.com/resource/frontend/v0.3.0/`.
- Status: `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Storage, Cortex, workers, and Relay healthy.
