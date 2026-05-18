# P131: Large-output and base64 leakage sweep

Status: done
Parent: P003
Root: P000
Source Ticket: T121 (split)
Source Check: none
Package: problems/P000/children/P003/children/P131
Body: problems/P000/children/P003/children/P131/README.md
Ticket(s): T249

## Problem
Even if the main projection path is correct, stale fallback branches, tests, docs, and utility helpers can keep old inline-base64 or full-output behavior alive. A targeted sweep is needed to classify and remove active leakage residues.

## Success Criteria
- Source sweeps for `base64`, `data:image`, `screenshot`, `payload_ref`, `step_ref`, and `include_display` are performed and summarized.
- Remaining hits are classified as active-safe, provider-boundary-only, test fixture, documentation, or stale/dead.
- Any active unsafe hit is fixed or split into a more specific child problem.
- Stale documentation or tests that teach old behavior are updated or removed.
- A final sweep shows no unexplained active leakage paths remain.

## Subproblems
- P255: Runtime large-output boundary sweep
- P256: Cortex projection and payload large-output sweep
- P257: Factory log redaction and detail large-output sweep
- P258: Final large-output leakage cross-scan

## Results
- R251

## Latest Check
C266

## Bodies
- Problem: problems/P000/children/P003/children/P131/README.md
- Ticket T249: problems/P000/children/P003/children/P131/tickets/T249.md
- Result R251: problems/P000/children/P003/children/P131/results/R251.md
- Check C266: problems/P000/children/P003/children/P131/checks/C266.md

## Follow-ups
- none
