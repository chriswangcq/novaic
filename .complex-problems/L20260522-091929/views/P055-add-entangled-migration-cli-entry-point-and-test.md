# P055: Add Entangled Migration CLI Entry Point And Test Coverage

Status: done
Parent: P049
Root: P000
Source Ticket: T046 (split)
Source Check: none
Package: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055
Body: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055/README.md
Ticket(s): T049

## Problem
The planner and executor must be exposed through a safe command-line entry point and verified as a complete offline migration command. This belongs under `P049` because operators need one command with clear flags, DSN-file support, failure behavior, and a redacted report before staging validation can run.

## Success Criteria
- A CLI entry point exists under `Entangled/packages/server-python/scripts/` or `[project.scripts]`.
- CLI arguments include SQLite source path, Postgres DSN or DSN file, report output path, explicit clean-target flag, target confirmation, and an optional dry-run/planning mode if implemented.
- DSN file contents are read for connection only and never printed or stored in reports.
- CLI failure messages avoid secret values.
- End-to-end command tests exercise safe failure without clean confirmation and a successful fixture/fake migration path that writes a report.
- `python -m py_compile` passes for new modules/scripts.
- Full Entangled server-python pytest passes.

## Subproblems
- none

## Results
- R045

## Latest Check
C046

## Bodies
- Problem: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055/README.md
- Ticket T049: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055/tickets/T049.md
- Result R045: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055/results/R045.md
- Check C046: problems/P000/children/P024/children/P027/children/P040/children/P049/children/P055/checks/C046.md

## Follow-ups
- none
