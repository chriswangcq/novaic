# P729: Runtime artifact manifest handling discovery

Status: done
Parent: P726
Root: P000
Source Ticket: T717 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729/README.md
Ticket(s): T718

## Problem
Discover how Runtime parses shell `tool-output.v1` artifact manifests, stores durable payload/raw data, and exposes LLM-visible bounded content for shell results.

## Success Criteria
- Runtime parser/handler for shell `tool-output.v1` manifests is identified with file pointers.
- Durable raw payload versus public LLM-visible content separation is identified.
- Tests proving bounded public shell text and durable raw payload behavior are identified or gaps recorded.
- Any active Runtime path that injects raw media/base64 into public tool content is listed.

## Subproblems
- none

## Results
- R709

## Latest Check
C753

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729/README.md
- Ticket T718: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729/tickets/T718.md
- Result R709: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729/results/R709.md
- Check C753: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P726/children/P729/checks/C753.md

## Follow-ups
- none
