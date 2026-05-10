# P000: File/display context architecture

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Systematically think through whether Xiaoma/Agent Runtime should use the filesystem, Blob/Cortex payload storage, and the `display` tool as the primary path for large visual/tool artifacts instead of repeatedly injecting large base64/display payloads into LLM context. The design should respect the product philosophy that the agent is the subject, the environment is secondary, the user is part of the environment, and shell/files/display are tools/resources the agent can intentionally access.

## Success Criteria
- Explain why the previous "just pass current_round_id" fix is necessary but not architecturally sufficient.
- Define an elegant resource model for large artifacts using files/blob/payload refs and explicit display access.
- Define how tool results, Cortex history, LLM context preparation, and user-facing monitor display should interact.
- Identify concrete design principles, invariants, risks, and migration phases.
- Produce a clear recommendation without requiring immediate code changes in this turn.

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
