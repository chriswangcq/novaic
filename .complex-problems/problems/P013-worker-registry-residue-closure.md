# P013: Worker Registry Residue Closure

Status: done
Parent: P006
Ticket: T013

## Problem

After P011/P012, tests and docs may still encode old assumptions such as
bespoke `_run_*` entrypoint sections. These residues are dangerous because they
invite future agents back into old implementation paths.

## Success Criteria

- Tests assert the new DSL shape instead of old per-worker function sections.
- Static scans reject `_configure_*`, `_run_*worker`, and handler lifecycle
  logic in business files.
- P006 and P002 can be closed with concrete test evidence.

## Result

- See `../results/R013-worker-registry-residue-closure.md`.

## Check

- See `../checks/C013-worker-registry-residue-closure.md`.
