# PR-145 — Entangled Schema and Config SSOT Residue Scan

| Field | Value |
| --- | --- |
| Status | `[scanned]` |
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

## Follow-up Decision

Delete the generated entity-id pipeline and replace any remaining checks with Entangled WS schema contract tests. The current generated artifacts conflict with Entangled schema SSOT.

## Unit / Guardrail Tests

- [ ] Cleanup follow-up should add an Entangled WS schema contract guardrail.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [ ] Cleanup follow-up must smoke App WS/entity sync.

## Git / Merge

- [ ] Commit ticket updates.
- [ ] Push parent docs update.
