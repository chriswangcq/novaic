# Check: Attach expected-generation validation audit

## Summary

Success. P327 is solved: the attach expected-generation path is now mapped and guarded end to end across dispatch/repository effect recording, session outbox payload delivery, and runtime attach handling. The audit found one real stale-scope race, fixed it, deleted stale helper residue, and added focused regression coverage for stale and missing generation cases.

## Evidence

- R319 summarizes child results P330-P333.
- C336 confirms repository attach recording now revalidates active saga/scope inside the same transaction as attach outbox creation, buffers stale requests, and removes `active_generation(...)` fallback residue.
- C337 confirms session outbox delivery rejects missing `expected_session_generation` before queue publish and preserves expected scope/generation on happy path.
- C338 confirms runtime attach handler rejects missing expected scope, missing expected generation, stale scope, and stale generation before mutating Cortex input.
- C339 confirms aggregate attach-generation coverage across repository, outbox, and runtime.
- Fresh focused verification passed:

```bash
PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr238_generation_checked_attach.py \
  tests/test_pr248_attach_outbox_cutover.py \
  tests/test_pr252_session_state_ssot.py \
  tests/test_pr267_session_outbox_effect_boundary.py \
  tests/test_pr233_active_inbox_dispatch.py \
  tests/test_pr255_legacy_compat_cleanup.py
# 31 passed in 0.21s
```

- Fresh residue guard passed:

```bash
! rg -n "active_generation\(|_active_session_generation_after_transaction|expected_session_generation\s*=\s*None" queue_service task_queue tests
# no matches
```

## Criteria Map

- Map attach request creation and payload fields, including expected generation: satisfied by P330/R315 and summarized in R319.
- Verify outbox worker and downstream handler preserve and enforce expected generation: satisfied by P331/C337 and P332/C338.
- Identify whether missing-generation or stale-generation attach payloads are rejected, ignored, or accepted: satisfied; missing generation is rejected at outbox/runtime, stale scope/generation is rejected or buffered before mutation depending on layer.
- Add or identify tests proving stale attach does not publish/mutate the wrong wake: satisfied by repository, outbox, runtime, and aggregate focused tests.

## Stress / Skepticism Notes

- This was not accepted solely from prose: I re-ran the focused test suite and the stale-helper source guard before marking success.
- The prior risky shape, where generation could be recomputed separately from the stale attach request scope, is directly covered by `test_attach_request_buffers_if_active_session_changes_before_record`.
- P327 does not claim to close finalize/session-ended generation ownership or rebuild fallback residue; those are correctly left to sibling problems P328 and P329.

## Result IDs

- R319
