# Rerun duplicate residue guard from repo root

## Problem

The P470 duplicate/residue guard failed to write its artifact because the command ran from `novaic-agent-runtime` with a repo-root-relative output path. Rerun the guard from the repo root and save the required artifact.

## Success Criteria

- Create `.complex-problems/L20260516-222011/tmp/p470/duplicate-residue-guard.txt`.
- Prove the adjacent duplicated `remaining_stack` string pattern is absent.
- Prove focused residue tests already passed or rerun them if needed.
