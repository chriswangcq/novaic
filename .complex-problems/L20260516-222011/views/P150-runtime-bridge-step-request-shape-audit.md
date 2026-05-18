# P150: Runtime bridge step request shape audit

Status: done
Parent: P148
Root: P000
Source Ticket: T133 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150/README.md
Ticket(s): T135

## Problem
Runtime-side code that sends step records to Cortex must construct the new structured observation/payload_ref shape. If it emits old inline result shapes, Cortex may reject active agent loops or lose payload refs.

This belongs under `P148` because active projection correctness depends on the producer as well as the Cortex endpoint.

## Success Criteria
- Runtime/Cortex bridge call sites that publish tool step records are mapped.
- Produced request shape contains `observation`, `step_ref`, and `payload_ref` where applicable.
- No runtime call site sends inline raw `result` as the durable tool result.
- Focused tests or source evidence prove the runtime producer uses the new contract.

## Subproblems
- none

## Results
- R129

## Latest Check
C143

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150/README.md
- Ticket T135: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150/tickets/T135.md
- Result R129: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150/results/R129.md
- Check C143: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P148/children/P150/checks/C143.md

## Follow-ups
- none
