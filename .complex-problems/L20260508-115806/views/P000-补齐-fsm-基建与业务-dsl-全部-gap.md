# P000: 补齐 FSM 基建与业务 DSL 全部 gap

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
补齐 FSM 基建与业务 DSL 全部 gap

## Success Criteria
- Action engines use explicit decision/effect plans with infrastructure adapters, not direct hidden business-side effects
- Worker assembly is shrunk into declarative DSL/specs with reusable infra policies
- Guardrails cover effect adapters, assembly thickness, docs status consistency, timestamp-aware deploy smoke, and process supervision
- Old paths/residue are removed or guarded; tests and docs prove no discounted gap remains

## Subproblems
- P001: Action engine effect-plan DSL
- P002: Declarative worker assembly DSL shrink
- P003: Effect adapter and assembly guardrails
- P004: Docs status consistency lint
- P005: Timestamp-aware deploy smoke
- P006: Runtime worker supervision
- P007: Final residue closure and verification

## Results
- R020

## Latest Check
C020

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R020: problems/P000/results/R020.md
- Check C020: problems/P000/checks/C020.md

## Follow-ups
- none
