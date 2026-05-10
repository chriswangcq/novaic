# Phase 5C.4 Documentation Residue Final Static Gate Result

## Summary

Ran the final Phase 5C residue gate and fixed additional current-contract documentation residues discovered by the gate. Current contract docs no longer advertise `_SKILL_LOCKS`, `_SCOPE_LOCKS`, `asyncio.Lock`, `_walk_scope_tree`, `include_display`, `format_for_llm`, or `scope_state_log` as current runtime authority.

## Done

- Ran the broad stale-term search across `docs/cortex`, `docs/architecture`, and `novaic-cortex/novaic_cortex`.
- Found real current-contract doc residue in:
  - `docs/cortex/invariants.md`
  - `docs/cortex/builtin-tools-and-skills.md`
- Updated `docs/cortex/invariants.md`:
  - Replaced old async-lock wording with scope lock manager wording.
  - Replaced `_SCOPE_LOCKS` / `_SKILL_LOCKS` snippets with `ScopeLockManager` / `get_lock_manager().release_key(...)` examples.
  - Replaced single-process deployment invariant with production Redis scope lock fail-closed invariant.
  - Kept SQLite active stack projection as the LIFO authority.
- Updated `docs/cortex/builtin-tools-and-skills.md`:
  - Replaced `_SKILL_LOCKS` / asyncio mutex wording with scope lock manager, Redis production backend, test-only in-memory manager, and best-effort key release.
- Rechecked current contract docs after the edits.

## Verification

- Broad audit command run:
  - `rg -n "_walk_scope_tree|include_display|scope_state_log|format_for_llm|Single-process service|in-memory caching|novaic-cortex-sandbox-|legacy DFS|fallback authority|local authority|process-local|in-process|_SKILL_LOCKS|asyncio\\.Lock" docs/cortex docs/architecture novaic-cortex/novaic_cortex -S`
- Current-contract negative gate:
  - `rg -n "_SKILL_LOCKS|asyncio\\.Lock|_SCOPE_LOCKS|_walk_scope_tree|include_display|format_for_llm|scope_state_log" docs/cortex/builtin-tools-and-skills.md docs/cortex/invariants.md docs/cortex/scope-lifecycle.md docs/cortex/internal-api-schemas.md -S`
  - returned no matches (`current_contract_exit=1`).
- Positive current-contract search was already run in P058 and shows SQLite projection / Redis lock manager wording in current docs.
- `python3 -m py_compile novaic-cortex/novaic_cortex/registry.py novaic-cortex/novaic_cortex/scope_locks.py` passed after the live-source docstring cleanup.

## Remaining Hit Classification

| Match Category | Files | Classification |
| --- | --- | --- |
| `_SKILL_LOCKS` in `docs/cortex/hardening-checklist.md` | historical checklist | Allowed historical material; file starts with a historical checklist banner and is retained for architecture-review traceability. |
| `_SKILL_LOCKS`, `_walk_scope_tree`, `asyncio.Lock` in `docs/cortex/architecture-review-2026-04-17.md` | historical review | Allowed historical source; explicitly dated architecture review. |
| `novaic-cortex-sandbox-*` in `docs/cortex/sandbox-shell.md` and `novaic_cortex/sandbox.py` | stable-path guard | Intentional negative guard: backing paths are ephemeral and shell commands using them are rejected. |
| `in-process` / `asyncio.Lock` in `novaic_cortex/scope_locks.py` | test helper / fail-closed guard | Intentional low-level backend implementation detail; production installs Redis and refuses to serve without it. |
| `include_display` in `novaic_cortex/step_result_projection.py` | low-level projection internals | Allowed internal helper flag for already-fetched data formatting; public `/v1/steps/read_formatted` API now uses explicit `projection`. |
| `legacy DFS` in `novaic_cortex/api.py` and context stack docs | negative current guard | Intentional "does not render legacy DFS tree" / old DFS renderer warning, not current authority. |
| `process-local` in `registry.py` / `store.py` | cache/test-only classification | Intentional: registry cache is not authority; local stores are test-only. |
| `fallback` in state-authority/context-event docs | negative design guard | Intentional "do not introduce fallback authority" or "fallback forbidden" wording. |
| `docs/architecture/**` non-Cortex hits | architecture history | Not Cortex current contract docs; retained as architecture/deployment history. |

## Known Gaps

- None for P060. Remaining broad-search hits are classified and are not current unowned authority residue.

## Artifacts

- `docs/cortex/invariants.md`
- `docs/cortex/builtin-tools-and-skills.md`
- Broad/static search output summarized in this result.
