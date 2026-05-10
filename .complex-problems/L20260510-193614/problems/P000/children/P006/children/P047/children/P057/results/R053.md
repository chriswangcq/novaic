# Phase 5C.1 Current Documentation And Comment Residue Audit Result

## Summary

Completed a read-only audit of current documentation and live comments. The main current-doc residues are `docs/cortex/scope-lifecycle.md` and `docs/cortex/internal-api-schemas.md`, which still describe `_walk_scope_tree` and `include_display`. The main live comment residue is `registry.py` describing Cortex as a single-process service with safe in-memory caching.

## Done

- Ran focused static searches over `docs` and Cortex source.
- Inspected high-risk current docs:
  - `docs/cortex/scope-lifecycle.md`
  - `docs/cortex/internal-api-schemas.md`
  - `docs/cortex/sandbox-shell.md`
  - `docs/cortex/state-authority-implementation-plan.md`
- Inspected high-risk live comments:
  - `novaic-cortex/novaic_cortex/registry.py`
  - `novaic-cortex/novaic_cortex/scope_locks.py`
  - `novaic-cortex/novaic_cortex/store.py`
  - `novaic-cortex/novaic_cortex/sandbox.py`

## Verification

- `rg -n "_walk_scope_tree|include_display|scope_state_log|format_for_llm|Single-process service|in-memory caching|novaic-cortex-sandbox-|legacy DFS|fallback authority|local authority|process-local|in-process" docs novaic-cortex/novaic_cortex -S`
- `rg -n "/v1/steps/read_formatted|scope_id.*unique|scope_projection|active_stack_projection" docs/cortex docs/architecture -S`

## Audit Map

- P058 current Cortex docs to edit:
  - `docs/cortex/scope-lifecycle.md`
    - Mentions `_walk_scope_tree` as root archive index helper.
    - Mentions `_walk_scope_tree(root_scope_path)` as child scope id uniqueness authority.
    - Still says API layer uses an `asyncio.Lock` `_SKILL_LOCKS`; current design uses Redis-backed lock manager and SQLite active stack projection.
  - `docs/cortex/internal-api-schemas.md`
    - `/v1/steps/read_formatted` still lists `include_display?`.
    - `skill_begin` uniqueness still says `_walk_scope_tree(root_scope_path)`.
- P059 live comments/docstrings to edit:
  - `novaic-cortex/novaic_cortex/registry.py`
    - Top-level docstring says "Single-process service (uvicorn), so in-memory caching is safe." This should become process-local cache/client wording under LogicalFS/SQLite authority.
- Keep as current guard/boundary wording:
  - `docs/cortex/sandbox-shell.md`
    - Correctly says `novaic-cortex-sandbox-*` backing paths are ephemeral and rejected; no edit required.
  - `novaic-cortex/novaic_cortex/sandbox.py`
    - Correctly rejects temp backing paths and local fallback behavior.
  - `novaic-cortex/novaic_cortex/scope_locks.py`
    - Comments describe in-process lock manager as a test/absence state and Redis as production; no edit required unless P059 finds phrasing to tighten.
  - `novaic-cortex/novaic_cortex/store.py`
    - Describes `MemoryStore` as local tests only; no edit required.
  - `novaic-cortex/novaic_cortex/api.py`
    - "legacy DFS tree" appears in a negative-contract comment; acceptable.
- Historical docs to leave untouched:
  - `docs/cortex/architecture-review-2026-04-17.md`
  - `docs/roadmap/tickets/PR-31-state-transition-log-tables.md`
  - `docs/roadmap/**` historical tickets/reviews unless a later check proves a file is being used as current architecture guidance.
- Current guard docs already useful:
  - `docs/cortex/state-authority-implementation-plan.md`
    - Explicitly bans in-process state, temp backing-path stability, and process-local fallback state.

## Known Gaps

- No source/docs changes were made in this audit ticket by design.
- P058 must update current Cortex docs.
- P059 must update live comments/docstrings.
- P060 must run the final static doc/comment gate.

## Artifacts

- `.complex-problems/tmp/impl-p5c-p1-result.md`
