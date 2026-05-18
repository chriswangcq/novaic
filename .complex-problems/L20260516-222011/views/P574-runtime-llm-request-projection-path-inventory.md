# P574: Runtime LLM Request Projection Path Inventory

Status: done
Parent: P564
Root: P000
Source Ticket: T568 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P574
Body: problems/P000/children/P005/children/P553/children/P564/children/P574/README.md
Ticket(s): T569

## Problem
Audit agent-runtime LLM request/context assembly paths to verify tool outputs, display perception, artifacts, and active stack messages are projected into LLM requests through the intended contract. This belongs under P564 because the recent regression appeared inside the LLM request body, where display/tool output was still visible as raw or misplaced content.

## Success Criteria
- Records exact scan commands and outputs for runtime request assembly, message conversion, tool-result projection, multimodal/image handling, and active stack injection.
- Reads relevant runtime code/test slices with line references.
- Classifies each hit bucket as intended, risky, removable, or follow-up.
- Separates valid current-turn image/perception content from invalid historical tool text or base64 embedding.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P578: Runtime Message Assembly And Active Stack Ordering Inventory
- P579: Provider Request Serialization And Multimodal Projection Inventory

## Results
- R567

## Latest Check
C603

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P574/README.md
- Ticket T569: problems/P000/children/P005/children/P553/children/P564/children/P574/tickets/T569.md
- Result R567: problems/P000/children/P005/children/P553/children/P564/children/P574/results/R567.md
- Check C603: problems/P000/children/P005/children/P553/children/P564/children/P574/checks/C603.md

## Follow-ups
- none
