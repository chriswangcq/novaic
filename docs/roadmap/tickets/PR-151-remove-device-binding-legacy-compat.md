# PR-151 — Remove Device Binding Legacy Compatibility

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-device, novaic-business, novaic-app if types are touched, docs |
| Depends on | PR-150 |

## Goal

Remove old device binding compatibility paths after verifying live data no longer needs them: list-format `mounted_tools`, old `agent.vm` fallback fields, and any legacy device lookup shape that is no longer a current product contract.

## Why This Matters

Device tool exposure is a security and UX boundary. Supporting multiple historical shapes makes it harder to know which mounted tools are truly active and which device config is authoritative.

## Current Suspects

- `novaic-device/device/agent_binding.py`
  - `normalize_mounted_tools(raw=list, ...)`
- `novaic-device/device/vm_routes.py`
  - fallback from `agent.devices` to `agent.vm`
- `novaic-device/device/agent_vm_proxy.py`
  - accepts legacy mounted tool list shape
- `novaic-business/business/device_client.py`
  - remote normalize-mounted-tools helper.
- `novaic-business/business/schema_push.py`
  - `agent-binding.mounted_tools` default shape.

## Implementation Plan

1. [x] Query/inspect live and local data for list-format `mounted_tools` and old `agent.vm` dependency.
2. [x] If no live data requires it, delete list-format normalization.
3. [x] Delete old `agent.vm` / `agent.devices` fallback in Device VM routes where binding is authoritative.
4. [x] Update Business and App types so the canonical mounted-tools shape is `Record<string, string[]>`.
5. [x] Add guardrail rejecting list-format mounted tools in active device/business code.

## Unit / Guardrail Tests

- [x] Device tests cover object-format mounted tools only: `PYTHONPATH=... python3 -m pytest tests` → 4 passed.
- [x] Business tests pass: `python3 -m pytest tests` → 175 passed.
- [x] App typecheck not needed; app types already use `MountedToolsByCategory = Record<string, string[]>`.
- [x] Guardrails reject legacy list normalization / old `agent.vm` fallback.

## Smoke / Deploy

- [x] Device tests pass.
- [x] Business tests pass.
- [x] Deployed Device and Business; both restarts brought all backends healthy.
- [x] Production smoke: Business and Device health endpoints return healthy; removed normalize endpoint is no longer registered (`POST` returns 405 on the old route shape).
- [x] Production evidence: `agent_device_bindings` has list-format `mounted_tools` = 0, object-format = 1.

## Git / Merge

- [x] Commit in `novaic-device`: `cd508f6 device: remove binding legacy compatibility`.
- [x] Commit in `novaic-business`: `53c0f20 business: require mounted tools object shape`.
- [ ] Parent repo submodule bump / docs commit.
- [x] Push `main`.
- [x] Mark this ticket `[deployed]` only after deploy evidence is collected.

## Closeout

Canonical `mounted_tools` is now an object keyed by category. Removed list-shape normalization RPC, Business normalization client, Device proxy fallbacks through `agent.devices`, VM route fallbacks through `agent.vm` ports/image path, and the unused subagent VM tools endpoint. Device VM start/status now read the authoritative `devices` entity row.
