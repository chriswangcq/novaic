# P000: Runtime current-round projection boundary

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
The Runtime `prepare_llm_call()` contract should pass the current round ID into Cortex step-ref expansion. Without this explicit input, expansion can treat historical tool results as current and allow display/image content from old rounds to re-enter the prompt. This is a core context-bloat guardrail for the shell/display migration.

## Success Criteria
- `prepare_llm_call()` passes `current_round_id=source.round_id` to `expand_messages_for_llm`.
- Unit tests assert the injected dependency receives the current round ID.
- Nearby Runtime contract tests still pass.
- The change is small and deterministic, with no hidden dependencies.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
