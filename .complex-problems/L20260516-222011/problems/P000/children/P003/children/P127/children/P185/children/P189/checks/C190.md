# P189 Check: runtime current display selection and active-stack ordering

## Summary

Success. R176 closes P189 through child checks P192 and P193: runtime selects current display projection correctly and preserves media despite a following active-stack system message.

## Evidence

- P192 proves projection selection with direct `read_step_formatted` projection assertions.
- P193 proves the active-stack-after-display scenario at `prepare_llm_call` level.
- Both children passed focused tests and recorded checks before this parent result.

## Criteria Map

- Runtime display projection selection code is mapped: satisfied by P192.
- Current display tool messages are assigned `display_perception` by metadata/currentness: satisfied by P192 tests covering tool name, metadata, and assistant tool-call inference.
- Following active-stack system message does not downgrade/drop media: satisfied by P193's active-stack-after-display regression.
- Display tool message remains placeholder/small after media extraction: satisfied by P193 placeholder assertions.
- Focused runtime/common tests pass: satisfied by recorded test runs in R176.

## Execution Map

- T178 was split into two children because the work had independent sub-outcomes.
- P192 closed projection selection.
- P193 closed active-stack media preservation.

## Stress Test

- Stale display reinjection is covered by P192: old display after newer shell becomes `history`.
- Active-stack ordering is covered by P193: final order is `assistant`, `tool`, `user(image)`, `system`.

## Residual Risk

- Provider/factory request serialization is still P190.
- End-to-end screenshot flow is still P191.

## Result IDs

- R176
