# Remove NDJSON Scope Transition Log Surface

## Problem Definition

After write/read cutover, the old NDJSON transition log surface is residue. Keeping it would leave misleading configuration, tests, and code paths that suggest scope transition history can still be file-authoritative.

## Proposed Solution

Physically remove the old surface:

- Delete `scope_state_log.py` and its direct tests.
- Remove `scope_state_log_path` from registry/workspace/main/startup/docs/tests.
- Remove `transition_log_path` parameters from `scope_state.transition` and `mark_archived`.
- Rewrite affected tests to use operational SQLite or omit transition persistence when not relevant.

## Acceptance Criteria

- No live code imports `scope_state_log`.
- No live code accepts or passes `transition_log_path`.
- No service startup arg or registry/workspace field named `scope_state_log_path` remains.
- Targeted tests pass.

## Verification Plan

- Run `rg` for old symbols.
- Run scope-state, scope-history, registry, operational-store tests.
- Run `py_compile` on modified modules.

## Risks

- Some older comments/tests may still describe NDJSON; they must be rewritten or removed.

## Assumptions

- No backward compatibility with old transition NDJSON files is required.
