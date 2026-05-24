# P000: Add Release Controller CI quality gate

Status: done
Parent: none
Root: P000
Source Ticket: none (none)
Source Check: none
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
NovAIC now has Release Controller-owned backend and LLM Factory deployment, but the quality gate inside that controller is still too thin: local developer unit tests are advisory, while Release Controller preflight only runs lightweight checks before building and deploying staging. The next correct step is to make CI quality enforcement an explicit Release Controller capability, so a pushed commit cannot become a staging release unless controller-run tests/guards pass, and prod promotion remains tied to a release that passed staging.

## Success Criteria
- Release Controller has a clear CI quality-gate model distinct from deploy smoke and direct manual scripts.
- Branch release plans run deterministic controller-owned quality gates before image build and before staging deployment.
- Gate failures block image build/deploy and are recorded as failed Release Controller runs.
- The default/sample configuration includes meaningful repo-level gates that can run in the controller worktree without relying on developer-local state.
- Tests cover quality-gate planning, execution ordering, and failure behavior.
- Documentation explains the development flow: local unit tests for fast feedback, Release Controller CI gate for authoritative staging admission, staging integration/smoke, and prod promotion from the passed release.
- Existing manual backend/factory deployment rejection remains intact.

## Subproblems
- P001: Implement first-class Release Controller quality gates
- P002: Configure and document the CI/CD quality gate flow
- P003: Roll out Release Controller quality gates on API host

## Results
- R009

## Latest Check
C011

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R009: problems/P000/results/R009.md
- Check C011: problems/P000/checks/C011.md

## Follow-ups
- none
