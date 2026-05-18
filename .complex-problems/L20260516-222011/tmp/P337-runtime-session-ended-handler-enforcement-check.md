# P337 Check: Runtime Session-Ended Handler Enforcement

## Verdict

`success`

## Criteria Map

- Map runtime/task handlers that process session-ended/finalize/skill-end/recovery completion: satisfied by P348.
- Verify handlers compare expected scope/generation against current root/session metadata before mutation: satisfied by P350/P352.
- Add or identify tests for missing expected scope, missing expected generation, stale scope, stale generation, and happy path: satisfied by P349/P350/P351/P352 test suites.
- Ensure stale handler calls do not append Cortex input, close a newer skill, or acknowledge/claim unrelated messages: satisfied by Cortex scope-end/session finalize guards and focused tests.
- Remove or flag handler paths that infer generation from current active state: satisfied after P351/P365 cleanup.

## Evidence

- P349 removed React contract default generation.
- P350 guarded Cortex finalize mutation by scope/generation identity.
- P351 guarded recovery/compensation finalize identity and removed startup rebuild fallback via P365.
- P352 aggregate verification passed: `170 passed in 0.95s`.
- Residue searches found no P337-scoped finalize-producing default identity path.

## Stress Test

The check spanned the whole runtime finalize path:

- upstream React contract construction,
- wake-finalize saga payloads,
- task handlers,
- Cortex archive mutation,
- session finalize/restart,
- recovery archive,
- saga compensation,
- startup rebuild.

The process found and fixed an indirect startup rebuild fallback before accepting the parent.

## Residual Risk

No known P337-scoped residual risk remains.
