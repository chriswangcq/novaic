# Ticket: Audit attach session outbox delivery

## Problem Definition

Verify `SessionOutboxDispatcher` delivery of attach input effects requires `expected_session_generation`, preserves it in the downstream task payload, and fails closed when the field is missing.

## Proposed Solution

Inspect `session_outbox.py` attach delivery code and `session_effects.py` payload builder. Run focused tests that cover attach effect shape, outbox delivery, missing generation, and session attach task payload. Add a guard if missing-generation delivery is not directly covered.

## Acceptance Criteria

- Attach outbox payload parsing and downstream task publish fields are mapped with file references.
- Missing `expected_session_generation` is rejected before task publish.
- Published `session.attach_input` task payload includes expected scope and expected generation.
- Verification includes focused outbox/effect tests.

## Verification Plan

Run source searches for `expected_session_generation` in `session_outbox.py`, `session_effects.py`, and related tests. Execute focused tests: `test_pr267_session_outbox_effect_boundary.py`, `test_pr248_attach_outbox_cutover.py`, and `test_pr255_legacy_compat_cleanup.py`.

## Risks

- The builder may preserve generation but the dispatcher may publish a different or partial payload.
- Missing-generation rejection may be covered by source guard only, not runtime behavior.

## Assumptions

- Outbox delivery is allowed to fail/dead-letter bad effects, but must not publish malformed attach tasks.
