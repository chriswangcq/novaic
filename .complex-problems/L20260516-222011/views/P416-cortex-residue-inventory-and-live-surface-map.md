# P416: Cortex residue inventory and live-surface map

Status: done
Parent: P404
Root: P000
Source Ticket: T405 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416/README.md
Ticket(s): T406

## Problem
Before modifying Cortex code, we need a precise Cortex-only residue inventory that excludes virtualenv/generated/cache files and separates live runtime surfaces from historical docs or ledger artifacts.

## Success Criteria
- Run Cortex-specific guards for generation defaults, active-state lookup, archive diagnostics, and context event lifecycle residue.
- Save guard outputs under the ledger tmp directory.
- Classify files into live code, tests, migration/scripts, docs/history, and generated/cache exclusions.
- Produce a live-surface map that downstream Cortex cleanup children can consume.
- Create follow-up children if the inventory reveals a slice too broad for the current plan.

## Subproblems
- none

## Results
- R400

## Latest Check
C426

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416/README.md
- Ticket T406: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416/tickets/T406.md
- Result R400: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416/results/R400.md
- Check C426: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P416/checks/C426.md

## Follow-ups
- none
