> **文档说明**：Entangled 订阅与本地缓存的**现行约定**（v0.1）；与全栈关系见 `docs/backend-architecture.md`。文中 `novaic-app/...` 路径以子模块 **`novaic-app`** 为准（如 `src/data/entangled/nav.ts`、`src-tauri/src/core/entangled_transport.rs`）。

# Sync Contract v0.1

Normative notes for Entangled subscription + local SQLite cache. Complements `HANDOVER.md` §十一 Path C.

## 1. Desired subscription set

Let **D** be the set of `(entity, params)` the client should hold on the wire after navigation settles.

**Inputs** (non-exhaustive): authenticated user, `route`, `agentId`, `settingsOpen`, component slots (`vm-{id}`).

**Source of truth (server-side table)**: `novaic-app/src-tauri/src/commands/nav.rs` → `route_subscriptions`.

**Invariant I4**: For a fixed input snapshot, **D** is deterministic (no hidden side channels).

## 2. Client ordering (TypeScript)

- All transitions on slot **`main`** MUST go through `navChanged()` / `navReleaseSlot()` in `src/data/entangled/nav.ts` so **`enqueueMainNav`** serializes IPC.
- Global shell → Rust main-slot route MUST use **`deriveDesiredMainNav()`** then **`navChanged`** in a **single** `useEffect` (`App.tsx`), so `home` / `conversation` / `settings` cannot be split across competing effects.
- **`bootstrapEntangledEntities()`** MUST NOT call `invoke('nav_changed')` directly; it MUST call `navChanged('home', {})` (Sync Contract Phase 1).

## 3. Rust ordering (per slot)

- For each **slot** name, the full sequence **release(old_specs) + acquire(new_specs)** for one `nav_changed` or `nav_release_slot` MUST NOT interleave with another call for the **same** slot at `.await` boundaries.
- **Implementation**: `NavState.slot_transition_locks` → `Arc<tokio::sync::Mutex<()>>` per slot; held for the whole command body after the in-memory spec swap.

## 4. Row identity (PK)

- Snapshot / head_n ingestion uses sync frame **`idField`** when present, else build-time `default_id_field_for_entity` (Rust) / `generated_entity_id_fields.json` (TS).
- **Invariant I1**: Rows without extractable PK MUST NOT be silently treated as “empty catalog”; `apply_snapshot` logs zero-insert vs partial-skip (`target: entangled_cache`).

## 5. Protocol version (`syncContractVersion`)

- **Advertised** on REST entangled schema (`{ entities, syncContractVersion }`) and on **Entangled Service** WebSocket as `IncomingMessage::Schema` (wire `syncContractVersion`), handled in `novaic-app/src-tauri/src/core/entangled_transport.rs`. Gateway mirrors the int in `gateway/entity/sync_contract.py`; Entangled WS uses `ws_handler.SYNC_CONTRACT_VERSION` — **keep both equal** when bumping. **Desktop:** entity sync frames and this schema path use Entangled WS (`/v1/sync`), not Gateway `AppBridge` `/api/app/ws`. The App WS channel may still emit a `push` / `schema`-style payload for TypeScript or other clients; it is **not** the primary carrier for Rust-side Entangled cache contract updates or sync frames.
- **v2** (`>= 2`): Server **must** send `idField` on snapshot/head_n sync frames (Gateway subscribe path already does). Rust logs **`metric=sync_frame_missing_id_field_v2`** at ERROR if a frame omits `idField` while the client’s stored contract version is ≥ 2 (still applies build-time fallback so the UI does not brick).
- Client stores the max advertised version from REST bootstrap (`entangled_set_sync_contract_version`) and from each Entangled WS `Schema` message (`entangled_transport`).

## 6. Observability (log targets)

- `entangled_sync_contract` — contract version updates; v2 missing-`idField` anomalies.
- `entangled_cache` — SQLite pool / snapshot anomalies (`snapshot anomaly: zero rows inserted`, etc.).
- `entangled_transport` — Entangled WS connection lifecycle; sync queue backpressure (`sync queue full — backpressuring`); slow `process_sync_with_contract`.
- `app_bridge` — Gateway `/api/app/ws` connection and message handling (pushes, WebRTC, gateway requests); **not** entity sync frames or Entangled sync-queue metrics.

## 7. References

- Execution checklist: `docs/sync-contract-execution-checklist.md`
- HANDOVER: “全局订阅 + 主键 + Sync Contract” 条目
- Desktop Entangled WS implementation: `novaic-app/src-tauri/src/core/entangled_transport.rs`
