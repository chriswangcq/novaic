# Sandbox Unused Filesystem Helper Cleanup

## Problem

Confirm whether the Sandbox filesystem helper surface is inactive. If inactive, delete it and remove exports/tests that keep dead code alive artificially.

## Success Criteria

- Usage scan proves whether helper is active.
- Inactive helper files/exports/tests are deleted rather than left as misleading residue.
- Sandbox focused tests pass after deletion.

