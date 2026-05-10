# Phase 5A Residue Audit And Classification Result

## Summary

Completed the audit-only pass for Phase 5 residue cleanup. The main live residue is not the already-deleted `resolve_active_scope_path` / `_collect_active_stack` path; it is the remaining `_walk_scope_tree` usage and wording around scope uniqueness/archive projection, plus a few current docs/comments that still describe file walking or in-memory/temp-path behavior in ways that need tightening. Historical review docs and tests that assert old paths stay deleted should be kept or classified, not blindly removed.

## Done

- Audited local transition-log authority patterns:
  - `scope_state_log.py` and `test_scope_state_log.py` are already deleted in the working tree.
  - Live source no longer references `scope_state_log` or local NDJSON transition authority.
  - `scripts/ci/lint_subagent_status.sh` only references an older roadmap ticket for another subsystem and is not Cortex live authority.
- Audited active-stack/file-walk residue:
  - Production Cortex no longer contains `_collect_active_stack` or `resolve_active_scope_path`.
  - `_walk_scope_tree` remains in `workspace.py` and live API call sites.
  - `skill_begin` uses `read_active_stack_projection` for active stack, but still does a file-tree cross-check for global child scope id uniqueness and comments call the filesystem "ground truth".
  - `archive_root_scope` uses `_walk_scope_tree` to materialize `/ro/scopes/_index.jsonl`; this is a projection/debug index, not LLM active-stack authority, but current docs should say so explicitly.
- Audited temp backing path behavior:
  - `sandbox.py` rejects `novaic-cortex-sandbox-*` backing paths and points users at `/cortex/ro` and `/cortex/rw`; this is a desired guard.
  - `tool_schemas` tests intentionally assert that the shell schema warns about `novaic-cortex-sandbox-*`; this should remain a guard.
  - Current docs should keep stable `/cortex/ro`/`/cortex/rw` wording and only mention backing paths as forbidden internal paths.
- Audited process-local/in-memory behavior:
  - `InMemoryScopeLockManager` is clearly test-only; production startup requires Redis.
  - `LocalFileStore`/`MemoryStore` remain test object-store adapters; production registry uses `BlobObjectStore` through LogicalFS authority.
  - `registry.py` has a "Single-process service (uvicorn), so in-memory caching is safe" comment that can be tightened because process memory must not be described as state authority.
- Audited compatibility/legacy wording:
  - Some tests are guard tests proving legacy behavior is removed; keep them.
  - `step_result_projection.py` has a "Compatibility wrapper" docstring for a wrapper still present; classify for P046 review.
  - `context_stack/budget.py` says "event-backed and legacy context preparation"; classify for P047 wording cleanup if current.
  - `operational_store.py` uses `payload_manifest_legacy` only inside schema migration; this is acceptable transitional migration code, not runtime fallback.

## Verification

- Ran static searches over `novaic-cortex/novaic_cortex`, `novaic-cortex/tests`, `docs/cortex`, `docs/architecture`, and `scripts`.
- Commands included:
  - `rg -n "scope_state_log|transition[_-]?log|scope_events\\.jsonl|state_log|append_transition|read_transition" ...`
  - `rg -n "resolve_active_scope_path|_collect_active_stack|active[-_ ]stack.*file|file[-_ ]walk|walk.*active|steps/.+active|active.*steps" ...`
  - `rg -n "novaic-cortex-sandbox|/tmp/novaic|backing path|/cortex/ro|/cortex/rw|\\$RO|\\$RW" ...`
  - `rg -n "fallback|compat|legacy|process-local|in-memory|authoritative|authority" ...`
  - `rg -n "_walk_scope_tree" ...`
  - `git -C novaic-cortex ls-files | rg "scope_state_log|transition.*log|legacy|compat" -n`
- Inspected representative code sections in `workspace.py`, `api.py`, `registry.py`, `store.py`, `scope_locks.py`, `main_cortex.py`, and existing guard tests.

## Known Gaps

- P046 should remove or replace live `_walk_scope_tree` authority usage where possible, especially the `skill_begin` duplicate-id filesystem cross-check and comments that call filesystem ground truth.
- P046 should confirm whether the `step_result_projection.py` compatibility wrapper remains needed or can be deleted/renamed.
- P047 should update current docs/comments around `_walk_scope_tree`, process-local caches, and old context/legacy wording.
- P048 should add/tighten static guards so `_collect_active_stack`, `resolve_active_scope_path`, forbidden `_walk_scope_tree` authority usage, and temp backing-path authority wording cannot re-enter.

## Artifacts

- Audit classification in this result.
- Child cleanup targets for P046-P048.
