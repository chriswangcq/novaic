# Round 002 Charter

## Round Window
- Start: 2026-02-20
- End: 2026-02-26
- Cadence: daily sync at 11:00, daily report cutoff at 18:00

## Objective
Complete Repo Cut Readiness for 8-repo split by closing all Week 1 critical gaps.

## In Scope
- Fix runtime startup/health stability
- Convert Storage-A/B from doc-only to executable delivery
- Complete gateway config and API surface deliverables
- Complete desktop RC installer and clean-machine startup validation
- Harden worker idempotency beyond in-process cache
- Add tools service concurrency/timeout reliability evidence
- Move shared-kernel from bridge mode toward real package adoption

## Out of Scope
- Production migration smoothing
- Backward compatibility for external users
- Large feature work unrelated to split readiness

## Success Criteria
- No open P0 at round close
- All 7 teams submit `DONE` or `DONE_WITH_GAPS` report with evidence
- Core cross-service startup path is reproducible by file-based runbook
- Round decision reaches `PASS` or `CONDITIONAL_PASS`

## Round Owner
- Program Owner: Wang Chaoqun
- Reviewer: AI Assistant + designated human reviewer
