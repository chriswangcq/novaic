# Verify Phase 2 Scope Transition SQLite Cutover

## Problem Definition

Phase 2 has split write cutover, history-read cutover, and old transition-log deletion into child work. Before closing the parent cleanup problem, we need a final verification pass that proves the active scope transition path is SQLite-only and that any remaining file-log references are either unrelated context event infrastructure or historical ledger text.

## Proposed Solution

Run a focused verification pass:

- Re-run targeted tests covering scope state transitions, history API reads, operational store behavior, and registry/startup dependency wiring.
- Run static searches for the old scope transition symbols and for generic NDJSON/log wording.
- Inspect remaining matches and classify them as removed, unrelated context-event infrastructure, or historical ledger/documentation.
- Record whether Phase 2 is ready for parent closure or requires a follow-up.

## Acceptance Criteria

- Targeted tests pass after the full write/read/delete sequence.
- No live code accepts, imports, or configures `scope_state_log`, `scope_state_log_path`, or `transition_log_path`.
- The history API reads from operational SQLite.
- Non-noop transition writes require `operational_store`.
- Remaining `event_log_path`/NDJSON matches, if any, are explicitly unrelated to scope transition authority.

## Verification Plan

- Run `pytest` for scope-state, scope-history API, operational-store, and registry dependency tests.
- Run `py_compile` on modified Cortex modules.
- Run `rg` for old scope transition symbols across product code, tests, docs, and startup scripts.
- Run `rg` for generic NDJSON/log markers and inspect any matches.

## Risks

- Generic context event-source infrastructure can look like residue if searched only by `event_log_path`; it must be classified carefully instead of deleted during this verification step.
- Some historical ledger files may still contain old terms by design and should not be treated as live product code.

## Assumptions

- Backward compatibility with old scope transition NDJSON files is not required.
- Phase 3 active-stack/status cutover is out of scope for this verification ticket.
