# Recovery and session-ended final verification

## Problem

After recovery stack diagnostics are hardened, run final focused tests and guards to prove recovery/session-ended compatibility cleanup is closed.

## Success Criteria

- Focused recovery/session-ended/finalize tests pass.
- Guard output classifies remaining recovery/session-ended hits.
- Any remaining fallback-looking behavior is either explicit/guarded or routed to a follow-up.
