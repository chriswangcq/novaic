# Cortex State Authority Implementation Plan

## Goal

Cortex should be a state-semantic service, not a long-lived in-process state
warehouse. The target model is typed state authority:

- SQLite owns durable operational state and queryable projections.
- LogicalFS/Workspace owns file/document/workspace authority.
- Redis owns short-lived coordination leases only.
- Blob owns raw bytes and artifact bodies only.
- Process memory owns rebuildable caches and service wiring only.

This document is the construction plan for moving from the current mostly-file
projection model to that target without creating a half-cutover.

## Non-Goals For This Chain

- Do not rewrite LogicalFS into a full live filesystem in this chain. That is a
  separate service program.
- Do not move raw bytes into Cortex SQLite. Blob remains the byte service.
- Do not keep compatibility branches indefinitely. Every phase needs a cleanup
  point.
- Do not introduce local fallback authority if SQLite, LogicalFS, Redis, or Blob
  is unavailable.

## Authority Map

| State kind | Authority | Allowed support stores | Notes |
| --- | --- | --- | --- |
| Scope lifecycle events | SQLite | Workspace trace export | Required for recovery and status. |
| Active stack/status | SQLite projection | Workspace trace export | Runtime should not walk trace files as authority after cutover. |
| LLM context events | Workspace event stream, then optional SQLite mirror | SQLite projection | Current source remains `context_events/events.jsonl` until a separate context-store cutover. |
| RO/RW files | LogicalFS/Workspace | Blob below LogicalFS | File operations should not bypass LogicalFS. |
| Distributed locks | Redis lease | SQLite generation/fencing | Redis is not semantic truth. |
| Large payload bytes | Blob | SQLite/Workspace manifest | Blob stores bytes; manifest stores meaning. |
| Observability logs | Logs/exporter | SQLite source events | Export failure must not change correctness. |
| Service caches | Process memory | none | Must rebuild after restart. |

## Phase 0: Construction Boundary

Write this document and identify module touch points.

Touch points:

- `novaic_cortex/operational_store.py`: new SQLite-backed store.
- `novaic_cortex/registry.py`: wire store into each `Workspace`.
- `novaic_cortex/workspace.py`: expose operational store dependency to scope
  operations.
- `novaic_cortex/scope_state.py`: record lifecycle events through the store.
- `novaic_cortex/api.py`: eventually read active stack/status from SQLite.
- `novaic_cortex/blob_payload.py` and `workspace.py`: eventually record payload
  manifests.
- `novaic_cortex/main_cortex.py`: require SQLite path at startup.

## Phase 1: SQLite Operational Store Substrate

Add a Cortex-local SQLite substrate with explicit dependencies.

Tables:

- `scope_events`
  - Append-only lifecycle/control events.
  - Indexed by `root_scope_id`, `scope_id`, and `occurred_at_ms`.
- `scope_projection`
  - Current scope phase, parent, generation, depth, skill/name/task.
- `active_stack_projection`
  - Current stack top and serialized frames per root scope.
- `payload_manifest`
  - Semantic manifest for Blob-backed payload bytes.

Rules:

- The store receives an explicit path and clock provider.
- Schema initialization is idempotent.
- SQLite runs in WAL mode.
- Writes are transactional.
- Idempotency keys are supported for events that can retry.

Exit criteria:

- Unit tests cover schema initialization, event append, projection upsert/read,
  active stack read/write, and payload manifest insert/read.
- No runtime path uses this store as authority yet; that happens in phase 2/3.
  This is acceptable because the phase is a substrate with tests, not a
  pretend cutover.

## Phase 2: Scope Transition Events To SQLite

Make SQLite the only durable authority for scope lifecycle transition history.

Rules:

- `scope_state.transition()` records a lifecycle event after canonical phase
  update succeeds.
- Idempotent self-loop does not append duplicate events.
- A non-noop transition without an operational store is a wiring error.
- SQLite write failure is loud; service logs are only human breadcrumbs.

Cleanup:

- Remove the old local transition-history module and startup surface.
- Keep context event-source files separate; they are not scope lifecycle
  authority.

Tests:

- Transition appends event.
- Self-loop does not append event.
- Restart can query lifecycle history from SQLite.
- Startup requires the operational SQLite path and no separate transition log.

## Phase 3: Active Stack/Status SQLite Cutover

Make SQLite projection the runtime authority for active stack and status.

Write path:

- `skill_begin` appends `ScopeOpened` and updates projections in one transaction.
- `skill_end` appends `ScopeClosed` and updates projections in one transaction.
- `finalize` appends `WakeFinalized` with `remaining_stack` and explicit reason.

Read path:

- `context/status` reads `active_stack_projection`.
- LIFO validation reads the SQLite top scope.
- Workspace `steps/_index.jsonl` and `meta.json` remain trace artifacts.

Migration:

1. Shadow-write SQLite projection while old file projection remains runtime
   authority.
2. Shadow-compare the historical file-walk control stack and SQLite projection.
3. Switch runtime reads to SQLite.
4. Delete or quarantine runtime file-walk authority.

Tests:

- Nested begin/end.
- Wrong-scope close rejected.
- Open child scope after restart still appears in stack.
- Finalize records remaining stack.
- Workspace trace write failure does not corrupt runtime stack.

## Phase 4: Blob Payload Manifest

Record semantic payload manifests outside Blob.

Manifest fields:

- `payload_ref`
- `source_payload_ref`
- `root_scope_id`
- `scope_id`
- `step_ref`
- `blob_ref`
- `mime_type`
- `size_bytes`
- `sha256`
- `status`
- `retention_class`
- `error`
- `created_at_ms`

Rules:

- Blob stores bytes only.
- Manifest stores meaning, source/final payload ref mapping, lifecycle, and
  structured failure state.
- Scope-local payloads use `retention_class="scope_local"` with no `blob_ref`.
- External payloads use `retention_class="external_blob"` and point at Blob raw
  bytes through `blob_ref`.
- Missing/corrupt/unavailable payload reads return structured `PayloadReadError`
  codes and update the manifest status.
- Retention sweeper reads manifests first, then deletes bytes.

## Phase 5: Cleanup And Guards

Remove residues after active cutovers:

- Local file-based transition authority.
- Runtime active-stack file walking.
- Stale comments saying in-process locks are production behavior.
- Temp backing-path language implying `/tmp/novaic-cortex-sandbox-*` stability.
- Any process-local fallback state.

Guards:

- Tests or grep guards for banned runtime authority paths.
- Startup readiness reports SQLite/Redis/LogicalFS/Blob backend health.
- Restart test proves no process memory is needed for recovery.
