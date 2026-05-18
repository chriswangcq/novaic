# Production side-effect callsite classification result

## Summary
Completed P484 as a read-only production call-site classification. The targeted scan found 73 raw lines and classified production side-effect surfaces into service/worker assembly boundaries, generic queue adapter APIs, durable session outbox dispatcher boundaries, session-owned outbox effect writers, generic worker effect executors, and docs/examples.

## Done
- Saved targeted raw production queries for `SagaOrchestrator`, direct publish calls, and session outbox effect terms.
- Built a classification table for each production call-site category.
- Routed `queue_service/routes.py:219` generic `/tasks/publish` direct publish decision to P485.
- Routed `session_outbox.py` direct side-effect outlet hardening to P486.
- Verified the child did not change production source.

## Verification
- Raw query artifact line count: `73`.
- Classification artifact lists file references and route decisions for all identified production categories.
- Before/after production git status diff shows no source delta except artifact header wording.

## Known Gaps
- P484 is intentionally classification-only.
- P485 must decide the generic task publish route boundary.
- P486 must harden the session outbox dispatcher boundary with guards/tests.

## Artifacts
- `.complex-problems/L20260516-222011/tmp/p484/production-side-effect-callsite-raw.txt`
- `.complex-problems/L20260516-222011/tmp/p484/production-side-effect-callsite-classification.md`
- `.complex-problems/L20260516-222011/tmp/p484/git-status-before.txt`
- `.complex-problems/L20260516-222011/tmp/p484/git-status-after.txt`
