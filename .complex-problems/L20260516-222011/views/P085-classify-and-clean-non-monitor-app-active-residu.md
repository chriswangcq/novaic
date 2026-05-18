# P085: Classify and clean non-monitor App active residue

Status: done
Parent: P066
Root: P000
Source Ticket: none (none)
Source Check: C085
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/README.md
Ticket(s): T077

## Problem
The active-code residue audit closed App monitor cleanup, but `novaic-app` still has non-monitor fallback/legacy/base64/compatibility hits that are not classified in the ledger. These may be benign UI behavior or test guards, but P066 cannot close until each active hit is classified and stale residue is cleaned.

## Success Criteria
- Run a bounded scan over `novaic-app/src` for fallback, compat, legacy, migration/migrate, TODO/FIXME, base64/data URLs, and direct-tool residue.
- Classify each non-monitor hit as active risk, intentional UI behavior, guard/test fixture, benign adapter, or stale residue.
- Apply safe cleanup for stale comments/names where possible without broad UI refactors.
- Run focused App tests/lint or document explicit no-code-change verification for classified benign hits.

## Subproblems
- P086: App settings and model config residue classification
- P087: App device WebRTC and UI media residue classification
- P088: App chat audio and blob upload residue classification
- P089: App non-monitor final residue scan and guard verification

## Results
- R077

## Latest Check
C090

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/README.md
- Ticket T077: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/tickets/T077.md
- Result R077: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/results/R077.md
- Check C090: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P085/checks/C090.md

## Follow-ups
- none
