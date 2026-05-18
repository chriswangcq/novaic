# P541 Lifecycle / Recovery Test Classification

## Source

- Input: `.complex-problems/L20260516-222011/tmp/p531/static-residue-tests.txt`
- Filtered hits: `.complex-problems/L20260516-222011/tmp/p541/lifecycle-recovery-test-hits.txt`
- Counts: `.complex-problems/L20260516-222011/tmp/p541/lifecycle-recovery-test-counts.txt`
- Context slices: `.complex-problems/L20260516-222011/tmp/p541/lifecycle-recovery-test-context.txt`

## Totals

- Hits: 108
- Files: 7

## Classification Table

| File | Hits | Purpose | Classification | Rationale | Follow-up |
| --- | ---: | --- | --- | --- | --- |
| `tests/test_pr254_finalize_ownership.py` | 42 | Finalize ownership and required stack payload | Expected regression/boundary coverage | Heavy `remaining_stack` and active-session vocabulary is intentional: this test suite enforces explicit finalize ownership, required stack snapshots, generation checks, and wake_finalize payload shape. | No |
| `tests/test_pr266_session_recovery_boundary.py` | 20 | Recovery marker and archive boundary | Expected regression/boundary coverage | `session_suspected_dead`, recovery metadata, and `remaining_stack` hits verify explicit recovery marker construction and rejection of malformed recovery archive payloads. | No |
| `tests/test_pr245_suspected_dead_recovery.py` | 12 | Suspected-dead recovery flow | Expected regression/boundary coverage | Hits assert wake_finalize failure records suspected-dead events, preserves active session state until recovery, and carries stack snapshots into recovery archive. | No |
| `tests/test_pr311_saga_compensation_outbox_cutover.py` | 12 | Saga compensation/outbox cutover | Expected regression/boundary coverage | Hits protect outbox-first behavior for wake saga/finalize failures and explicitly assert no direct suspected-dead method call remains. | No |
| `tests/test_pr233_active_inbox_dispatch.py` | 9 | Active inbox dispatch and recovery interaction | Expected regression/boundary coverage | `active_session`, `session_suspected_dead`, and `remaining_stack` hits are tied to dispatch decisions, recovery saga context, and inbox preservation. | No |
| `tests/test_pr247_recovery_outbox_cutover.py` | 8 | Recovery outbox publisher contract | Expected regression/boundary coverage | Hits verify recovery archive payload requires `remaining_stack` and flows through the outbox/publisher boundary. | No |
| `tests/test_scope_end_environment_notifications.py` | 5 | Scope-end archive and environment notification lifecycle | Expected regression/boundary coverage | Hits verify scope-end archive passes `remaining_stack` and input message IDs through Cortex bridge semantics. | No |

## Conclusion

All P541 hits are intentional lifecycle/recovery regression coverage. No stale or misleading test residue was found in this group.
