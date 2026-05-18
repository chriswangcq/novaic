# Compatibility residue guard inventory

## Problem

The project needs a concrete guard inventory before cleanup. Broad searches must enumerate optional/missing/stale generation compatibility patterns across runtime queue code, task handlers, Cortex code, tests, and migration-like files, then classify which areas require deeper child work.

## Success Criteria

- Run source guards covering generation/session_generation/expected_generation/finalize_generation/current_generation defaulting, optional branches, active lookup, and active clear/restart/archive helpers.
- Include runtime queue code, task handlers/sagas/contracts, Cortex code, tests, and migration-like directories in the search scope.
- Produce a hit matrix with file references and initial classification buckets.
- Identify which hits are already safe due to explicit validators/tests and which require child cleanup.
- Do not change implementation code in this inventory child.
