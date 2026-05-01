# PR-151 — Remove Device Binding Legacy Compatibility

| Field | Value |
| --- | --- |
| Status | `[ ]` |
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

1. [ ] Query/inspect live and local data for list-format `mounted_tools` and old `agent.vm` dependency.
2. [ ] If no live data requires it, delete list-format normalization.
3. [ ] Delete old `agent.vm` / `agent.devices` fallback in Device VM routes where binding is authoritative.
4. [ ] Update Business and App types so the canonical mounted-tools shape is `Record<string, string[]>`.
5. [ ] Add guardrail rejecting list-format mounted tools in active device/business code.

## Unit / Guardrail Tests

- [ ] Device tests cover dict-format mounted tools only.
- [ ] Business available-tools tests pass.
- [ ] App typecheck passes if types are touched.
- [ ] Guardrail rejects legacy list normalization / old `agent.vm` fallback.

## Smoke / Deploy

- [ ] Device tests pass.
- [ ] Business tests pass if touched.
- [ ] Deploy Device and Business if needed.
- [ ] Production smoke: Host Desktop, Linux VM, and Android mounted tools still resolve correctly.
- [ ] Production evidence: data scan confirms no list-format mounted tools remain.

## Git / Merge

- [ ] Commit in each touched repo.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark this ticket `[deployed]` only after deploy evidence is collected.

