# Session Finalize Diagnostics Binding Check

## Summary

Not successful yet. The audit found the main implementation shape is likely correct, but the one-go ticket explicitly left blocking verification gaps. Given the acceptance criteria require stale/valid finalize diagnostics to be bound and protected from future drift, source inspection plus loose existing tests is not enough.

## Blocking Gaps

- Valid finalize is not yet protected by an exact assertion that `session_closed` metadata equals the explicit finalize metadata produced before mutation.
- Stale generation and stale scope rejection tests do not yet assert the rejected payload contains the rejected finalize's own reason, generation, scope, and remaining stack while emitting no valid `session_finalized` event.
- Focused tests and residue search have not been rerun after hardening the assertions.

## Result IDs

- R351
