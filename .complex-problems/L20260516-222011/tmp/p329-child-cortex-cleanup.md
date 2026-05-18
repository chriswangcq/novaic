# Cortex compatibility residue cleanup

## Problem

Cortex context/operational/archive paths may still contain compatibility residue around generation defaults, active-state lookup, archive diagnostics, or context event lifecycle. Any live Cortex residue found by the inventory must be removed and tested.

## Success Criteria

- Inspect all Cortex hits from the inventory matrix.
- Remove dangerous Cortex compatibility branches or replace them with explicit validators.
- Preserve legitimate diagnostic/projection/counter behavior only with explicit classification.
- Add focused Cortex tests for every changed live boundary.
- Rerun Cortex-focused tests and Cortex guard searches until no unclassified Cortex residue remains.
