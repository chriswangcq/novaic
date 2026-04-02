# Sync Contract — execution checklist

Status: `[ ]` todo · `[x]` done · `[~]` in progress

## Phase 0 — Spec + baseline

- [x] **0.1** `docs/SYNC_CONTRACT.md` v0.1 (this program)
- [x] **0.2** Audit: `invoke('nav_changed'` only in `nav.ts` (bootstrap 已改 `navChanged`)
- [x] **0.3** Audit: Rust batch writes — `apply_snapshot` / `prepend_older` take explicit `id_field`; `apply_delta` uses server op `id`; pending merge uses `default_id_field_for_entity` per entity (see `cache.rs`)

## Phase 1 — Subscription lifecycle

- [x] **1.1** `bootstrapEntangledEntities` → `navChanged('home')` (`entangledBootstrap.ts`)
- [x] **1.2** Per-slot `tokio::sync::Mutex` for full `nav_changed` / `nav_release_slot` (`nav.rs`)
- [x] **1.3** Automated: `npm run verify:sync-contract-schema`（需 `GATEWAY_URL` + 可选 `SYNC_CONTRACT_TEST_TOKEN`）；**manual**：桌面清缓存冷启动仍建议每版 spot-check models/skills/devices
- [x] **1.4** `deriveDesiredMainNav` + 单一 main-slot effect（`nav.ts` + `App.tsx`）；Vitest：`npm run test:unit`

## Phase 2 — PK / schema (next)

- [x] **2.1** REST entangled schema includes `idField` (gateway)
- [x] **2.2** `entity_prepend_page` / prepend uses same `id_field` as sync (Rust)
- [x] **2.3** Snapshot `inserted==0` observability (warn/metric)

## Phase 3 — Protocol version

- [x] **3.1** Schema push + REST: `syncContractVersion` (`ws_handler`, `gateway/entity/sync_contract.py`, TS `loadSubscriptionSchema`, `entangled_set_sync_contract_version`, AppBridge `schema` push)
- [x] **3.2** v2: client ERROR log if snapshot/head_n missing `idField` when contract ≥ 2 (`process_sync_with_contract`); server subscribe/notifier already send `idField`

## Phase 4 — Observability + HANDOVER

- [x] **4.1** Structured tracing (`entangled_sync_contract`, `entangled_cache`, `metric=` fields) — scrape via log pipeline / dashboard TBD
- [x] **4.2** HANDOVER updated；CI：`tauri-ci.yml` 含 `tsc`、`test:unit`、`npm run lint`、`novaic-gateway` Sync Contract unittest；`novaic-gateway/.github/workflows/ci.yml` 含同上 unittest
