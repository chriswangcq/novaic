# PR-134 — Keep Cortex step result projection as the sole result path

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Scope | `novaic-cortex`, `novaic-agent-runtime`, `novaic-app`, config/scripts/docs |
| Depends | PR-86..PR-98, PR-130..PR-133 |
| Goal | Make Cortex steps the only tool-result owner. Provider-facing result expansion uses Cortex step-result projection helpers. |
| Non-goal | Add another result plane, Gateway result endpoint, App lazy-fetch path, or compatibility aliases. |

## Background

Cortex owns scope trees, steps, tool outputs, and folded summaries. The intended structure is:

1. Tool execution stores normalized output in the Cortex step.
2. LLM context assembly renders normal tool messages from Cortex.
3. Provider expansion uses `read_step_formatted` / `read_step_preview`.
4. Entangled execution logs may carry a lightweight `result_id` join key, but the underlying result remains a Cortex step.

## Implementation Checklist

- [x] Keep Cortex result projection in `novaic_cortex.step_result_projection`.
- [x] Update Cortex API imports and public exports to use the new module name.
- [x] Keep Runtime provider expansion wrapper in `step_result_client`.
- [x] Update LLM handler imports/comments to describe Cortex step-result projection.
- [x] Change Runtime deterministic `result_id` prefix to `step-result:`.
- [x] Delete App result client and unused diagnostic `LogDetail` renderer.
- [x] Remove unused locale key for removed diagnostic UI.
- [x] Remove obsolete result-path startup/config entries.
- [x] Delete obsolete one-off migration script if no active call path depends on it.
- [x] Update current docs that describe active Cortex/App modules.

## Tests

- [x] Cortex unit tests for step result projection and context engine.
- [x] Runtime unit tests for LLM context expansion and execution-log metadata.
- [x] App unit tests for execution log rendering and no visible result-id/debug leakage.
- [x] Static search guard: no active code references removed result-path identifiers, removed service prefixes, removed clients, removed Gateway endpoints, or removed config.

## Smoke Test

- [x] Send a simple chat message; confirm execution log rows still show semantic agent-monitor text.
- [x] Expand agent monitor rows; confirm no technical result-fetch failure is shown.
- [x] Trigger a tool call that stores a result; confirm Cortex step contains the result and LLM context can expand it through `read_step_formatted` (unit smoke).

## Deploy / GitHub

- [x] Commit Cortex changes separately or as one PR-134 commit if all subrepos are tested together.
- [x] Deploy affected services: Cortex, Runtime, App. (`./deploy services`, `./deploy frontend 0.3.0`, 2026-05-01)
- [x] If configs/scripts are used on the target host, deploy those too. (`novaic-common`, Runtime config, App resources, and `/opt/novaic/start.sh` synced by deploy script)
- [x] Record production evidence: no separate result process expected; no Gateway result endpoint frontend request; fresh execution log `result_id` starts with `step-result:`.

Production evidence recorded 2026-05-01:

- `./deploy status` green for Entangled, Gateway, Business, Device, Queue, File, Cortex, and workers.
- Remote active-code grep found no removed result-path identifiers in Cortex/Runtime/Common active paths.
- Remote `ss`/`pgrep` found no separate result process.
- Recent Cortex/Queue/Worker logs had no `ERROR`, `Traceback`, `ModuleNotFoundError`, or `ImportError`.
- Frontend OTA `https://relay.gradievo.com/resource/frontend/v0.3.0/` returned HTTP 200.
