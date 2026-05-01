# PR-145 — Entangled Schema and Config SSOT Residue Scan

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | Entangled, common, business, gateway, app, scripts |
| Depends on | PR-144 |

## Goal

Ensure Entangled schema/config is sourced from one path and clients consume it consistently. No generated stale app schema, duplicated endpoint config, or ad-hoc shell parsing should remain in active startup paths.

## Scan Plan

1. [x] Search schema generation and schema cache paths.
2. [x] Search Entangled endpoint and WS URL ownership.
3. [x] Search config readers for non-strict ad-hoc parsing.
4. [x] Search App/Rust cache for generated stale entity contracts.

## Findings

- Current architecture doc says the intended SSOT clearly: Entangled direct WS sends schema, Gateway only discovers/syncs endpoint, and there is no REST schema fallback.
- `scripts/start.sh` now uses strict config loading; `scripts/ci/check_start_config_contract.py` guards against mirrored/ad-hoc config parsing.
- Old generated entity-id pipeline remains:
  - `scripts/generate_entity_types.py` still generates App entity types/id fields from Business/Device `schema_push`.
  - `scripts/sync_entity_id_fields.sh` still copies Gateway-generated id fields into App paths.
  - `scripts/check_entity_store_pk.py` still expects `novaic-app/src/data/entangled/generated_entity_id_fields.json`, which has already been removed.
  - `novaic-gateway/gateway/entity/generated_entity_id_fields.json` still exists.
  - `scripts/gateway/export_entity_id_fields.py` still generates the Gateway JSON artifact.
- `scripts/deploy-business.sh` still includes subscriber canary config overlays, which overlaps PR-143 rather than schema SSOT.

## Implementation

- Deleted the stale entity TS generator and generated `novaic-app/src/data/entities/__generated__.ts` artifact.
- Replaced the only App dependency on the generated TS file with a local `AgentMemoryEntity` type.
- Deleted the stale generated id-field pipeline:
  - `scripts/sync_entity_id_fields.sh`
  - `scripts/check_entity_store_pk.py`
  - `scripts/gateway/export_entity_id_fields.py`
  - `novaic-gateway/gateway/entity/generated_entity_id_fields.json`
- Removed CI steps that compared/generated stale schema artifacts.
- Added `scripts/ci/lint_entangled_schema_ssot.sh` and wired it into both lint and Tauri CI.

## Follow-up Decision

Generated artifacts are deleted. App-facing schema contract tests now rely on live/backend Entangled contract files and the runtime WS schema loader; the old Python codegen/id-field JSON path is banned from active paths.

## Unit / Guardrail Tests

- [x] Added Entangled schema SSOT guardrail.
- [x] `npm run test:unit -- --run src/data/entangled/client.test.ts src/data/entities/entangledEntityContracts.test.ts`

## Smoke / Deploy

- [x] `npx tsc --noEmit --pretty false`
- [x] `./scripts/ci/lint_entangled_schema_ssot.sh`

## Git / Merge

- [x] Implementation ready for commit in this batch.
- [x] Parent docs updated.
