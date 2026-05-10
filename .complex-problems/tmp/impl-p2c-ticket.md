# Cut Scope History Reads To SQLite And Remove NDJSON

## Problem Definition

Scope transition writes are now on SQLite, but `/v1/scope/history`, startup configuration, registry/workspace constructors, direct transition parameters, `scope_state_log.py`, and old tests still preserve the NDJSON path. Phase 2C must remove the old authority path rather than leave compatibility residue.

## Proposed Solution

Split into read cutover, physical cleanup, and verification:

- Route `/v1/scope/history` to `OperationalSqliteStore` via `scope_transition_events.list_scope_transition_events`.
- Remove `scope_state_log_path` from Cortex startup, registry, workspace, docs, and tests.
- Remove `transition_log_path` from `scope_state.transition/mark_archived`.
- Delete `scope_state_log.py` and its NDJSON tests.
- Verify static searches and targeted tests.

## Acceptance Criteria

- `/v1/scope/history` returns rows from SQLite operational store.
- No required startup argument or registry/workspace constructor field for `scope_state_log_path` remains.
- No `transition_log_path` transition parameter remains.
- Old NDJSON helper/test files are deleted.
- Targeted tests pass and static searches show no old authoritative NDJSON transition path.

## Verification Plan

- Run scope state, operational store, registry dependency, and relevant API/history tests.
- Run `rg` for `scope_state_log`, `scope_state_log_path`, and `transition_log_path`.
- Inspect git diff for physical deletion.

## Risks

- Some tests may use NDJSON helpers directly and require rewrite rather than deletion.
- API history response currently includes `log_path`; this field should be removed or replaced with an explicit backend indicator.

## Assumptions

- No backward compatibility with old NDJSON transition logs is required.
