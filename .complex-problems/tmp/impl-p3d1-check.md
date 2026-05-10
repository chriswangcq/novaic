# Archive Finalize Stack Snapshot Cutover Success Check

## Summary

P035 is solved. R029 cuts the archive/finalize stack snapshot source from file-walk to SQLite active-stack projection and verifies both behavior and static source boundaries.

## Evidence

- `scope_end` root archive branch now reads `read_active_stack_projection(...).frames`.
- `scope_end` child archive branch now reads `read_active_stack_projection(...).frames`.
- Existing root/wake/child archive tests were strengthened with monkeypatch failures for `_collect_active_stack(...)`.
- A static guard asserts the `scope_end` section has no `_collect_active_stack`.
- Targeted tests passed: 25 tests.
- Full Cortex suite passed: 454 tests.

## Criteria Map

- Root and child `scope_end` archive paths derive active stack frames from `read_active_stack_projection(...)`: satisfied.
- `_append_wake_archived_event(...)` and `_finalize_active_stack_for_archive(...)` receive projection-derived frames: satisfied by the shared `active_stack` replacement feeding both calls.
- Idempotent already-archived archive paths keep existing API behavior: satisfied, those early returns were unchanged and existing retry test still passes.
- Tests cover root archive, wake child archive with remaining stack, and archive retry/idempotency behavior: satisfied by updated lifecycle tests.

## Execution Map

- T032 was classified `one_go`.
- R029 recorded the implementation result and verification output.
- No follow-up is needed for P035 itself; remaining residue belongs to sibling P020 child problems.

## Stress Test

- Monkeypatch tests make the old `_collect_active_stack(...)` path fail immediately if archive/finalize accidentally calls it.
- Static section guard catches reintroduction even if runtime tests miss a branch.
- Full suite confirms the projection cutover did not regress archive, lifecycle, or context event behavior.

## Residual Risk

- `_collect_active_stack(...)` remains elsewhere by design for later child problems P036/P037/P039.
- Wake creation projection seeding is still a known later residue and is outside P035.

## Result IDs

- R029
