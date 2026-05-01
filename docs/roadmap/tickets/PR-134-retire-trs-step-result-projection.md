# PR-134 — Retire TRS and keep Cortex step result projection

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Scope | `novaic-cortex`, `novaic-agent-runtime`, `novaic-app`, config/scripts/docs |
| Depends | PR-86..PR-98, PR-130..PR-133 |
| Goal | Remove the TRS concept and old service/client paths. Tool outputs live in Cortex steps; optional LLM projection is a Cortex step-result projection helper. |
| Non-goal | Reintroduce a separate Tool Result Service, Gateway `/api/trs/*`, App TRS lazy fetch, or compatibility aliases. |

## Background

Cortex now owns scope trees, steps, and folded summaries. The old TRS mental model adds a second result plane and creates misleading code paths:

- Runtime deterministic `result_id` still uses the `trs:` prefix.
- Cortex helper module is named `trs.py` even though it reads Cortex steps.
- Runtime wrapper is named `trs_client.py`.
- App still ships an unused TRS service client and diagnostic result renderer.
- Dev scripts and config still mention `tool_result_service`.

The intended structure is simpler:

1. Tool execution stores normalized output in the Cortex step.
2. LLM context assembly renders normal tool messages from Cortex.
3. When a tool result must be converted for provider input, Cortex exposes `read_step_formatted` / `read_step_preview`.
4. Entangled execution logs may carry a lightweight `result_id` join key, but it is a Cortex step-result id, not TRS.

## Implementation Checklist

- [x] Rename Cortex `novaic_cortex.trs` to `novaic_cortex.step_result_projection`.
- [x] Update Cortex API imports and public exports to use the new module name.
- [x] Rename Runtime `task_queue.utils.trs_client` to `step_result_client`.
- [x] Update LLM handler imports/comments to describe Cortex step-result projection.
- [x] Change Runtime deterministic `result_id` prefix from `trs:` to `step-result:`.
- [x] Delete App TRS service client and unused TRS diagnostic `LogDetail` renderer.
- [x] Remove unused locale key `empty_trs`.
- [x] Remove Tool Result Service from active dev startup scripts and App services config.
- [x] Delete one-off TRS migration script if no active call path depends on it.
- [x] Update current docs that describe active Cortex/App modules.

## Tests

- [x] Cortex unit tests for step result projection and context engine.
- [x] Runtime unit tests for LLM context expansion and execution-log metadata.
- [x] App unit tests for execution log rendering and no visible result-id/debug leakage.
- [x] Static search guard: no active code references `TRS`, `trs:`, `task_queue.utils.trs_client`, Gateway `/api/trs/*`, or `tool_result_service` except explicitly archived docs.

## Smoke Test

- [ ] Send a simple chat message; confirm execution log rows still show semantic agent-monitor text.
- [ ] Expand agent monitor rows; confirm no old result-service 404/debug lazy fetch is attempted.
- [x] Trigger a tool call that stores a result; confirm Cortex step contains the result and LLM context can expand it through `read_step_formatted` (unit smoke).

## Deploy / GitHub

- [ ] Commit Cortex changes separately or as one PR-134 commit if all subrepos are tested together.
- [x] Deploy affected services: Cortex, Runtime, App. (`./deploy services`, `./deploy frontend 0.3.0`, 2026-05-01)
- [x] If configs/scripts are used on the target host, deploy those too. (`novaic-common`, Runtime config, App resources, and `/opt/novaic/start.sh` synced by deploy script)
- [x] Record production evidence: no `Tool Result Service` process expected; no Gateway `/api/trs` frontend request; fresh execution log `result_id` starts with `step-result:`.

Production evidence recorded 2026-05-01:

- `./deploy status` green for Entangled, Gateway, Business, Device, Queue, File, Cortex, and workers.
- Remote active-code grep found no `TRS`, `trs:`, `trsid`, `trs_client`, `tool_result_service`, `tool-result-service`, `api/trs`, `Tool Result Service`, or `migrate_trs` references in Cortex/Runtime/Common active paths.
- Remote `ss`/`pgrep` found no `:19994`, `main_tool_result_service`, `tool-result-service`, or `novaic-storage-b`.
- Recent Cortex/Queue/Worker logs had no `ERROR`, `Traceback`, `ModuleNotFoundError`, or `ImportError`.
- Frontend OTA `https://relay.gradievo.com/resource/frontend/v0.3.0/` returned HTTP 200.
