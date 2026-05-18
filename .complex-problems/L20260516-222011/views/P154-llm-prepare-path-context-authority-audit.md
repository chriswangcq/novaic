# P154: LLM prepare path context authority audit

Status: done
Parent: P143
Root: P000
Source Ticket: T137 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154
Body: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/README.md
Ticket(s): T140

## Problem
The active LLM prepare-context path must not read `context.jsonl` as authoritative conversation context. It should use ContextEvent/read-model projections. This audit must prove the current prepare path authority.

This belongs under `P143` because it is the highest-risk source of duplicate/stale context and payload leakage.

## Success Criteria
- Active prepare-context/read-model path is mapped with source pointers.
- Evidence proves it does not call `read_context` or parse `context.jsonl` as authority.
- If any authority read exists, it is fixed or split into a blocking child problem.

## Subproblems
- P156: Cortex prepare_for_llm read model authority
- P157: Runtime LLM prepare caller authority
- P158: LLM prepare authority residue guard

## Results
- R138

## Latest Check
C152

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/README.md
- Ticket T140: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/tickets/T140.md
- Result R138: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/results/R138.md
- Check C152: problems/P000/children/P003/children/P126/children/P134/children/P143/children/P154/checks/C152.md

## Follow-ups
- none
