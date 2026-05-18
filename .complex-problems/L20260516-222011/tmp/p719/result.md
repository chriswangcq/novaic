# Business/subscriber code dependency boundary audit result

## Summary

Audited Business/subscriber active code for hidden env/config reads and ownership leaks. The subscriber aggregation path is already explicit-config based and guard tests pass. Two small active code wording residues were patched: an old `Gateway owns subagent` helper comment/docstring and a `[Gateway]` log prefix in Business subagent spawn code.

## Done

- Confirmed subscriber aggregation config is loaded at the process boundary in `novaic-business/main_subscriber.py` via `load_im_aggregation_config_from_env(os.environ)` and injected into `DispatchSubscriber`.
- Confirmed `_group_for_aggregation` in `novaic-business/business/subscribers/dispatch_subscriber.py` uses `self.aggregation_config`, not dynamic env reads.
- Confirmed subscriber code comments state notification semantic lifecycle and Cortex scope input ownership remain with Runtime/Cortex, not Subscriber.
- Patched `novaic-business/business/internal/helpers.py` to replace stale `B2: Gateway owns subagent` / `Gateway business APIs` wording with Business-owned product subagent wording.
- Patched `novaic-business/business/internal/subagent.py` to replace a stale `[Gateway] Created SUBAGENT_SEND...` log prefix with `[Business]`.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider novaic-business/tests/test_im_aggregation.py novaic-business/tests/test_pr153_lifecycle_guardrails.py novaic-business/tests/test_pr117_task_proxy_removed.py` passed: `26 passed in 0.49s`.
- Focused scan for `B2: Gateway owns subagent`, `For Gateway business APIs`, `[Gateway] Created SUBAGENT_SEND`, `scope/append_input`, `subscriber_append_input`, and `TaskManager API` across Business code/tests returned only intentional guard-test references for the forbidden strings.
- Reviewed `git -C novaic-business diff -- business/internal/helpers.py business/internal/subagent.py` to confirm the intended cleanup is present. Note: `business/internal/subagent.py` already had unrelated local doc/comment edits before this ticket; they were left intact.

## Known Gaps

- No production behavior change was intended or made beyond log/comment wording.
- Final cross-surface verification remains for P720.

## Artifacts

- Changed: `novaic-business/business/internal/helpers.py`
- Changed: `novaic-business/business/internal/subagent.py`
- Test command: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider novaic-business/tests/test_im_aggregation.py novaic-business/tests/test_pr153_lifecycle_guardrails.py novaic-business/tests/test_pr117_task_proxy_removed.py`
