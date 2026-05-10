# Audit Active Stack Authority Boundaries

## Problem Definition

Phase 3 must not blindly replace `_collect_active_stack` call sites. Some stack logic is runtime control authority, some belongs to semantic context-event projection, and some is trace/debug/test behavior. We need a precise call-site map before implementation.

## Proposed Solution

Perform a read-only audit:

- Inspect `api.py`, `workspace.py`, context event projection/read-model modules, operational store, and relevant tests.
- Catalog every runtime active-stack/status read and write path.
- Classify each path as control authority, semantic context projection, trace/debug, or test-only.
- Identify the concrete next changes for Phase 3B/C/D.

## Acceptance Criteria

- `_collect_active_stack`, `context_status`, `skill_begin`, `skill_end`, finalize, and stack-projection paths are cataloged.
- The audit distinguishes SQLite operational control stack from context event semantic stack.
- The next implementation tickets have explicit boundaries and no ambiguous stack source remains unclassified.

## Verification Plan

- Use `rg` and targeted source reads.
- Record file/line evidence for each category.
- Cross-check against Phase 3 success criteria and existing tests.

## Risks

- `stack` terminology is overloaded; accidental conflation with context event projection would produce the wrong architecture.
- A shallow grep may miss indirect helpers used by runtime APIs.

## Assumptions

- This audit performs no production code changes.
- Subsequent child tickets will implement the migration based on the audit map.
