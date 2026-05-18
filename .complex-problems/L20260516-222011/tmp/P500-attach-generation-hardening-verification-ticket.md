# Attach generation hardening verification ticket

## Problem Definition

P500 must independently verify the P499 attach builder hardening. It should prove focused attach/session tests pass, the optional builder generation contract is gone, attach-race buffering still works, and there is no active no-generation `SESSION_ATTACH_INPUT` delivery path.

## Proposed Solution

Run the focused attach/session pytest suite and targeted source guards after the P499 implementation. Save all evidence under the P500 ledger tmp directory. Inspect guard output for remaining optional generation contracts or direct no-generation `SESSION_ATTACH_INPUT` publication.

## Acceptance Criteria

- Focused attach/session pytest suite passes.
- Guard output has no `expected_session_generation: int | None` or `expected_session_generation=None` hits.
- Attach-race buffering tests are included in the passing suite.
- Guard output shows attach publication still flows through generation-aware builder/outbox paths.

## Verification Plan

- Run `python -m pytest tests/test_pr238_generation_checked_attach.py tests/test_pr248_attach_outbox_cutover.py tests/test_pr255_legacy_compat_cleanup.py tests/test_pr267_session_outbox_effect_boundary.py tests/test_pr271_session_attach_flow_consolidation.py tests/test_pr273_session_harness_final_residue_guard.py`.
- Run targeted `rg` guards over `novaic-agent-runtime/queue_service` and relevant tests.
- Review the P499 source diff once more during verification.

## Risks

- Guard output can be noisy because tests intentionally mention some contract strings.
- Passing focused tests do not equal full runtime e2e; this ticket is scoped to attach generation hardening only.

## Assumptions

- P499 is the only implementation change being verified here.
