# P160: Runtime Cortex prepare handler contract map

Status: done
Parent: P135
Root: P000
Source Ticket: T146 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P135/children/P160
Body: problems/P000/children/P003/children/P126/children/P135/children/P160/README.md
Ticket(s): T150

## Problem
The runtime Cortex handler and bridge translate a saga action into a Cortex `prepare_for_llm` call and return a prepared snapshot. That response shape must be explicit and stable, otherwise later handlers may fall back to local continuity fields.

## Success Criteria
- `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py` and `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` are mapped around `prepare_for_llm`.
- The response fields returned to the saga are documented, including messages, tools, active stack metadata, and any compatibility fields.
- Any fallback to `read_context` or local continuity inside the prepare handler/bridge is classified and fixed or split if it can affect provider messages.
- Focused handler/bridge tests are identified and run.

## Subproblems
- P166: Cortex prepare handler response shape map
- P167: CortexBridge prepare_for_llm endpoint contract map

## Results
- R148

## Latest Check
C162

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P135/children/P160/README.md
- Ticket T150: problems/P000/children/P003/children/P126/children/P135/children/P160/tickets/T150.md
- Result R148: problems/P000/children/P003/children/P126/children/P135/children/P160/results/R148.md
- Check C162: problems/P000/children/P003/children/P126/children/P135/children/P160/checks/C162.md

## Follow-ups
- none
