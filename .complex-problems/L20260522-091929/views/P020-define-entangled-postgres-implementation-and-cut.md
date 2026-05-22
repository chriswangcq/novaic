# P020: Define Entangled Postgres Implementation and Cutover Requirements

Status: done
Parent: P009
Root: P000
Source Ticket: T015 (split)
Source Check: none
Package: problems/P000/children/P004/children/P009/children/P020
Body: problems/P000/children/P004/children/P009/children/P020/README.md
Ticket(s): T018

## Problem
After inventory and semantic mapping, Entangled still needs a concrete implementation and cutover requirements plan: target database, schema/adapter phases, migration tooling, validation matrix, WebSocket/client smoke tests, rollback boundaries, and residue cleanup rules. This plan must avoid production cutover during P009.

This belongs under P009 because it turns Entangled's migration risks into actionable requirements for later implementation tickets without changing production yet.

## Success Criteria
- A phased implementation plan exists for Postgres config, adapter boundary, schema generation, store SQL conversion, migration tooling, tests, and deployment.
- The plan targets the existing `novaic_entangled` Postgres database and states whether any local SQLite unit-test fake remains acceptable.
- Pre-cutover and post-cutover checks are specified for table row counts, schema/index parity, sync-version equality/monotonicity, sample JSON decode, transition history, and health/readiness.
- WebSocket/client smoke tests are specified for schema push, representative list/form/stream full sync, create/update/delete delta, and reconnect behavior.
- Rollback boundaries are documented for before PG writes, after PG writes with no client-visible deltas, and after client-visible deltas.
- Old SQLite cleanup criteria are defined for the stabilization window.
- No production Entangled cutover is attempted by this child problem.

## Subproblems
- none

## Results
- R015

## Latest Check
C015

## Bodies
- Problem: problems/P000/children/P004/children/P009/children/P020/README.md
- Ticket T018: problems/P000/children/P004/children/P009/children/P020/tickets/T018.md
- Result R015: problems/P000/children/P004/children/P009/children/P020/results/R015.md
- Check C015: problems/P000/children/P004/children/P009/children/P020/checks/C015.md

## Follow-ups
- none
