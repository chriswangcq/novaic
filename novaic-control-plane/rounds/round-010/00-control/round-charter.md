# Round 010 Charter

## Window
- Round ID: `round-010`
- Round status: `ACTIVE`
- Cadence notes: blocker sync + report submission within the round.

## Objective
- Convert Round 009 "format pass" into "remote-operable pass":
  - increase commit reachability quality from all-`SKIP_REMOTE` to verifiable `REACHABLE`,
  - remove local-layout assumptions from replay/runbook artifacts.

## Scope
- Publish canonical GitHub org/repo mapping for all split repos.
- Update team reports and operability artifacts to clean-clone remote execution paths.
- Strengthen commit reachability gate from "no UNREACHABLE" to "minimum REACHABLE coverage".
- Keep existing evidence contract strict (machine-readable fields only).

## Out of Scope
- Large feature redesign unrelated to split operability.
- Non-blocking UX/documentation polishing that does not affect gate outcomes.

## Success Criteria
- `commit-reachability-audit.md` includes at least one `REACHABLE` pair per team.
- `cross-team-evidence-audit.md` remains zero findings.
- No report relies on local-only repo addressing (`file:///`, sibling-path assumptions without remote fallback).
- Round gate runner prints final PASS marker for round-010.
