# PR-294 — Session Legacy Residue Cleanup

Status: Closed

## Goal

Delete live compatibility naming and shadow-key active paths once the new
FSM/outbox path is the only active logic.

## Scope

- Remove no-generation attach compatibility branches after migration.
- Remove `shadow:*` active-path event keys after event vocabulary cutover,
  retaining only an explicit historical-key alias for upgrade dedupe.
- Delete old tests whose only purpose was dual-path compatibility.
- Update docs banners that describe obsolete transition architecture.

## Dependencies

- PR-286 through PR-293.

## Risks

- Premature cleanup can delete needed migration compatibility.
- Incomplete cleanup leaves misleading code residue.

## Acceptance Criteria

- Grep checks show no active legacy branch markers except migration comments or
  explicit historical-key alias adapters.
- Old compatibility tests are removed or renamed to current behavior tests.
- Docs reflect the current single path.

## Verification

- Grep residue audit.
- Full runtime suite.

## Closure Notes

- Removed retired race attach/race buffer event vocabulary through PR-294A.
- Removed live-code compatibility naming around session event key helpers:
  `CompatSessionEventKeyPrefix` / `compat_event_key` became
  `SessionEventKeyPrefix` / `session_event_key`.
- Current session event keys now emit `session:*` prefixes only. PR-297 removed
  the previous historical `shadow:*` alias lookup under the no-backcompat
  runtime policy.
- Removed unused synchronous wake creation publish wrapper and unused outbox
  append wrapper from `SessionOutboxDispatcher`.
- Residue guards assert no active session harness code contains retired
  active-session/pending-trigger language, direct saga creation, direct active
  state mutation, or race-attach consume paths.
- Verified by residue/vocabulary tests and full runtime suite:
  `pytest` in `novaic-agent-runtime` -> 357 passed.
