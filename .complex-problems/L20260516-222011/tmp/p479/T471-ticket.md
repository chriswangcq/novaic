# Rerun duplicate residue guard from repo root ticket

## Problem Definition

P470 needs the duplicate/residue guard artifact that failed to write because of cwd. This follow-up reruns the guard from the repository root.

## Proposed Solution

Run a Python/string guard and `rg` residue guard against `session_outbox.py`, saving output to `.complex-problems/L20260516-222011/tmp/p470/duplicate-residue-guard.txt`.

## Acceptance Criteria

- The guard artifact file exists.
- It reports `duplicate_adjacent_remaining_stack= False`.
- It reports the current remaining-stack literal count.
- Any broad residue hits are reviewed or recorded.

## Verification Plan

Inspect the saved guard artifact.

## Risks

- None beyond command/path mistakes.

## Assumptions

- Prior focused tests already passed in R465.
