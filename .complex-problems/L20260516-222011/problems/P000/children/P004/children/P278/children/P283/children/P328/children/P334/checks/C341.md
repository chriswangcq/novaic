# Check: Finalize/session-ended entry-point inventory

## Summary

Success. R320 satisfies the inventory problem: it maps the live finalize/session-ended entry points, records what identity fields are carried, identifies existing tests, and produces concrete downstream targets for the unsafe or incomplete paths. Because this was a one-go inventory, I cross-checked with an additional broad source search before accepting it.

## Evidence

- R320 maps normal finalize producers, `wake_finalize`, `session.ended`, HTTP/client boundaries, repository/FSM mutation, pending restart, saga compensation/recovery, Cortex archive, skill-end lifecycle, and startup rebuild.
- R320 explicitly identifies the key risk: missing `session_generation` can become `generation=0`, and finalize FSM currently treats zero as an implicit current-generation fallback.
- R320 lists existing tests for finalize contract, FSM reject behavior, ledger facts, pending restart, recovery archive, and Cortex scope_end behavior.
- Additional check found 193 source matches for finalize/session/recovery/generation terms and the mapped live paths match those high-signal results.

## Criteria Map

- List every finalize/session-ended/recovery/watchdog/restart/skill-end entry point with references: satisfied for live paths in R320.
- Record carried fields: satisfied; R320 maps saga/scope/generation/reason/remaining-stack/pending/restart where each applies.
- Classify safe/unsafe/downstream: satisfied; unsafe generation-zero and rebuild fallback paths are delegated to P335-P339/P329.
- Identify current tests: satisfied in R320 coverage map.
- Produce follow-up targets: satisfied by downstream targets P335-P339.

## Execution Map

- T325 was executed as a bounded, read-only one-go inventory.
- No implementation files were changed by T325.
- The execution used multiple `rg` passes plus direct file inspection of session repository, FSM, wake finalize, session handlers/routes/client, saga compensation, recovery, outbox, Cortex scope_end, rebuild, and tests.

## Stress Test

- I did not trust the first search only; I re-ran a broader combined search for `wake_finalize`, `session_ended`, `CORTEX_SCOPE_END`, `SESSION_ENDED`, suspected-dead, recovery archive, `mark_active_states_no_active`, `remaining_stack`, `finalize_reason`, and `session_generation`.
- The broad source search returned 193 matches, and R320 accounts for the live non-test boundaries surfaced by those matches.
- The check intentionally did not close the identified unsafe `generation=0` behavior; it is routed to downstream implementation tickets.

## Residual Risk

No blocking residual risk for P334 as an inventory problem. The real behavioral risks remain intentionally open in child/sibling work:

- P335/P336/P337/P339: missing/zero generation and stale finalize enforcement.
- P338: recovery archive and remaining-stack/reason semantics.
- P329: startup rebuild generation fallback residue.

## Result IDs

- R320
