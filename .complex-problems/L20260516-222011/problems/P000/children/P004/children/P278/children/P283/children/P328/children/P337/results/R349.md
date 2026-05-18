# T336 Result: Runtime Session-Ended Handler Enforcement

## Child Problems Closed

- P348: Runtime finalize handler inventory.
- P349: React contract positive session generation.
- P350: Cortex finalize mutation identity guards.
- P351: Recovery compensation finalize identity.
- P352: Runtime finalize enforcement aggregate verification.

## Implemented Outcome

- Runtime finalize-producing contracts no longer default missing `session_generation` to `0`.
- Wake-finalize payload builders require positive generation before building session-ended and cortex scope-end payloads.
- Cortex scope-end handler requires positive generation before archive mutation.
- Session-ended handler, client, route, and repository enforce explicit finalize reason, positive generation, and remaining stack.
- Recovery/compensation paths now require positive generation before synthesizing wake-finalize or recovery archive scope-end work.
- Startup rebuild no longer fabricates active session generation from missing saga context identity.
- Stale attach-publish naming residue was updated to the current outbox-recording semantics.

## Verification

- P352 aggregate verification compiled relevant modules.
- P352 aggregate verification ran the focused runtime finalize suite: `170 passed in 0.95s`.
- Residue searches for generation/default/finalize paths were inspected and classified.

## Gap

No P337-scoped gap remains.
