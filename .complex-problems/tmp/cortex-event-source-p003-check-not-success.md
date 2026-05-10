# P003 check: replay watermark gap

## Result IDs

- R017

## Evidence

- R017 proves the pure projector exists and covers message, notification, scope, fold, stale sibling, and tool result behavior.
- Focused tests pass: `63 passed`.
- Existing context tests pass: `29 passed`.
- Full Cortex suite passes: `418 passed`.
- Static scans show no forbidden projector dependencies and no accidental endpoint cutover.

## Criteria Map

- A pure replay/projector can derive prepared LLM messages and active stack from events: satisfied.
- Projection handles wake start, system prompt, notification hint, assistant message, tool step, skill begin, skill end, and wake archive events: satisfied.
- Tests cover fold behavior, nested skills, stale open sibling suppression, tool result placement, and notification hint semantics: satisfied.
- Projection output is generation-checked and can be rebuilt from event stream: partially satisfied only. The snapshot has `applied_seq`, and projection rejects mixed root ids, but it does not yet enforce ordered contiguous event sequence, same stream id, or expose a stream watermark sufficient for strict generation checks.

## Execution Map

- Phase 2 child problems P014-P017 closed successfully.
- The parent result R017 aggregated their outcomes.
- The remaining issue is not endpoint integration; it is a stricter replay-integrity requirement inside the pure projector contract.

## Stress Test

- Static scans and tests prove no hidden IO or live cutover.
- The unresolved case is a malformed event list with missing/duplicated/out-of-order seq or mixed stream ids. Current projection can accept some of these instead of failing deterministically.

## Residual Risk

- If left unresolved, later read-path cutover could rely on a snapshot without a strong event-stream watermark, making recovery/attach generation checks weaker than the intended FSM/event-source model.

## Verdict

Not success. Create a small follow-up to make projection replay integrity explicit before Phase 2 can close.
