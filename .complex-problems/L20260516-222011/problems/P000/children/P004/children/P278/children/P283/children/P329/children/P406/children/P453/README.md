# Aggregate compatibility guard matrix rerun

## Problem

Final compatibility verification needs a clean aggregate source guard matrix after all runtime, Cortex, and test/migration cleanup children are closed.

## Success Criteria

- Save final source/test guard matrix excluding dependency/cache/ledger noise.
- Classify retained hits by category: validator, rejection reason, test guard, projection, display/media boundary, generic infrastructure, or unresolved risk.
- Identify any dangerous or unclassified residue for follow-up.
