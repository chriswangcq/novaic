# Cortex State Authority Audit Result

## Summary

Current Cortex is mostly aligned with the target model:

> Cortex is a state-semantic service; durable semantic authority should live in LogicalFS/Workspace files, and the Cortex process should not become a long-term state store.

The core durable paths are now Workspace/LogicalFS backed:

- LLM context is prepared from the ContextEvent source stream at `<root_scope_path>/context_events/events.jsonl`.
- Workspace file authority is built from LogicalFS object-store adapters under per-agent owner prefixes.
- Shell `/cortex/ro` and `/cortex/rw` are materialized views of Workspace files; RW changes are observed as patches and written back to Workspace.
- Cortex process memory mainly holds service wiring and caches, not canonical long-lived conversation state.

This is not yet the mathematically perfect form where every observable stateful concern is one unified event-sourced Workspace model. There are still intentional operational planes outside Workspace authority.

## Evidence

Checked these code paths:

- `novaic-cortex/novaic_cortex/context_event_store.py`
  - `ContextEventStore.event_log_path()` writes/read source events at `<root_scope_path>/context_events/events.jsonl`.
  - `read_events()` reads through `Workspace.read(...)`.
  - `append_event()` appends through `Workspace._sys_append_line(...)` and requires explicit clock/id providers.
- `novaic-cortex/novaic_cortex/registry.py`
  - `WorkspaceRegistry` caches `BlobObjectStore` per user and `Workspace` per `(user_id, agent_id)`.
  - Cache entries are adapters; durable state is in LogicalFS/Blob-backed Workspace.
- `novaic-cortex/novaic_cortex/workspace_authority.py`
  - LogicalFS owner prefix is `agents/{agent_id}`.
  - `build_workspace_file_authority(...)` returns `StoreBackedLogicalFileAuthority`.
- `novaic-cortex/novaic_cortex/logical_fs.py`
  - `MountNamespaceLogicalFS._workspace_snapshot()` reads Workspace `/ro/` and `/rw/` into a snapshot.
  - `release_view()` observes LogicalFS patch and applies changes back to Workspace `/rw`.
- `novaic-cortex/novaic_cortex/api.py`
  - `/v1/context/prepare_for_llm` uses `ContextEventReadModel` over the ContextEvent stream.
  - `_collect_active_stack()` still walks projection files (`steps/_index.jsonl`, scope `meta.json`) for operational control/status.
- `novaic-cortex/novaic_cortex/scope_locks.py`
  - Production requires Redis scope locks; in-memory locks are test-only.
- `novaic-cortex/novaic_cortex/scope_state_log.py`
  - Scope transition history is a local best-effort NDJSON ops log, not canonical authority.
- `novaic-cortex/novaic_cortex/blob_payload.py`
  - Large raw tool payload bytes are stored in Blob Service with `blob://cortex-payload/...` refs.

## Current State Assessment

Already good:

- Cortex is no longer the durable owner of LLM context state.
- Context assembly is event-stream based instead of old DFS reconstruction in the production `prepare_for_llm` path.
- Workspace/LogicalFS is the semantic file authority for scopes, summaries, context events, and shell-visible `/ro`/`/rw`.
- The shell sandbox view is an ephemeral materialization/cache, not canonical storage.
- Process-local registry state is rebuildable after restart.

Not perfect / remaining seams:

- Redis lock state is outside Workspace. It is coordination/lease state, not business truth, but correctness depends on it during concurrent mutations.
- Large payload bytes are externalized to Blob Service. Workspace keeps refs/semantics; Blob owns raw bytes. This matches the "Blob is cheap file server" model, but strictly means not all durable bytes live inside Workspace files.
- `scope_state_log_path` writes local NDJSON. It is explicitly best-effort observability and canonical phase is in `meta.json`, but it is still a persistent local file outside LogicalFS.
- `_collect_active_stack()` still derives operational stack status from materialized scope projection files instead of a pure ContextEvent projection.
- `logical_fs.py` currently uses acquire snapshot + release patch, not a continuously live server-side filesystem stream.
- `scope_locks.py` has stale top-of-file prose saying "Today the implementation is asyncio.Lock" even though production later requires Redis. This is documentation residue.

## Answer

So the answer is:

It is mostly true today, for durable semantic state and LLM context authority. Cortex is behaving like a semantic service over Workspace/LogicalFS rather than an in-process state warehouse.

But it is not physically perfect yet. There are still separate operational state planes:

- Redis for mutation serialization.
- Blob Service for large raw payload bytes.
- Local NDJSON for scope transition observability.
- Projection-file walking for active stack/status.
- Snapshot/patch shell filesystem semantics rather than fully live LogicalFS.

## Recommended Follow-Ups

If the target is "perfect state-authority purity", split follow-up tickets:

1. Move or reclassify `scope_state_log_path` into an explicit observability service/log plane, or persist it through LogicalFS if it must be queryable state.
2. Replace `_collect_active_stack()` projection walking with a ContextEvent-derived control projection, or explicitly document projection files as the control-state materialized view.
3. Clean stale `scope_locks.py` module header so docs match Redis-mandatory production behavior.
4. Clarify Blob payload contract: Workspace owns semantic refs; Blob owns raw bytes; no direct semantic authority in Blob.
5. Decide whether LogicalFS should remain snapshot/patch per shell invocation or evolve into a live mounted/streaming filesystem service.
