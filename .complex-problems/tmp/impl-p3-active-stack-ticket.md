# Cut Active Stack And Status Authority To SQLite

## Problem Definition

Runtime control stack/status still derives authority from scope projection files via `_collect_active_stack()` and related file-walk paths. Phase 3 must move the authoritative active stack/status read/write path to the operational SQLite projection, while keeping workspace files as trace/artifact output only.

## Proposed Solution

Split Phase 3 into small closure problems instead of attempting one large migration:

- Audit every active-stack/status read and write path in Cortex APIs, Workspace lifecycle methods, context status, LIFO validation, finalize, and tests.
- Introduce a small active-stack projection adapter over `OperationalSqliteStore` with explicit frame schema and generation semantics.
- Shadow-write stack projection on skill begin/end/finalize while preserving current API behavior.
- Cut runtime reads and LIFO validation to SQLite projection.
- Quarantine or remove `_collect_active_stack()` runtime authority paths, leaving file-walk only as repair/debug if truly needed.
- Verify restart recovery, nesting, mismatch, finalize remaining-stack recording, open-child behavior, and residue searches.

## Acceptance Criteria

- `skill_begin`, `skill_end`, and `context_status` read/write active stack projection from operational SQLite.
- LIFO mismatch checks use SQLite top-of-stack, not file walking.
- Finalize records explicit reason and remaining stack into durable events/projection.
- Projection-file walking is removed from the runtime authority path or isolated behind clearly named repair/debug code.
- Tests cover nesting, wrong-scope close, open child after restart, finalize/open stack behavior, and old path residue.

## Verification Plan

- Run focused audit searches for `_collect_active_stack`, context status, skill begin/end, finalize, and stack projection code.
- Add or update targeted tests around `context_skill_begin`, `context_skill_end`, `context_status`, restart/rebuild, and mismatch behavior.
- Run static residue searches proving file-walk authority is gone from runtime paths.
- Run targeted Cortex tests and `py_compile` on modified modules.

## Risks

- This touches the control-plane hot path; doing it as one huge edit risks half-cutover behavior.
- Existing context event projection also has a stack model; the SQLite operational control stack must have a clear boundary from semantic LLM context projection.
- Some old tests may assert file-projection internals and need rewrite, not compatibility preservation.

## Assumptions

- Operational SQLite store from Phase 1 is available for every registry-built workspace.
- No backward compatibility is required for old runtime file-walk authority.
- Workspace files may remain as trace artifacts, but not as the live control authority.
