# Preserve wake finalize compensation context

## Problem Definition

When wake/think/actions sagas fail, compensation creates a `wake_finalize` saga with too little context. It drops the root scope id, wake scope path, session generation, stack snapshot, and round metadata needed for `cortex_scope_end` and `session_ended`.

## Proposed Solution

Update saga compensation context construction to preserve explicit finalize/session/root metadata from the failed saga context. Do not invent fallback values for missing upstream fields; copy the values that are present.

## Acceptance Criteria

- Compensation `wake_finalize` context includes `agent_root_scope_id`, `wake_scope_path`, `session_generation`, `round_num`, and remaining-stack metadata when present on the failed saga context.
- Regression tests prove the durable outbox effect and published finalize saga preserve those fields.
- Regression tests prove wake-finalize payload builders can use the preserved context for `cortex_scope_end` and `session_ended`.

## Verification Plan

- Extend saga compensation outbox tests.
- Run focused saga compensation/finalize ownership tests.

## Risks

- Adding fallback guesses would hide upstream contract bugs; avoid them.
- Existing production stuck session still needs deploy/recovery verification.

## Assumptions

- Normal wake/think/actions saga contexts already contain the needed root/path/session metadata; the compensation builder is the narrowing point that caused the observed failure.
