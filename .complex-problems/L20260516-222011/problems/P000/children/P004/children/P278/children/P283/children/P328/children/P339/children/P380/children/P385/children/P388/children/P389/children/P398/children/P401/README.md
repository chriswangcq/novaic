# Widened guard residue matrix

## Problem

The widened guard still reports many generation-like, round, retry, and counter defaults across runtime and Cortex code. Some are harmless counters, but the project needs a final explicit matrix proving no live generation authority residue remains.

## Success Criteria

- Rerun the widened guard after the live-boundary children are complete.
- Classify every remaining hit into live session authority, event sequencing, round number, retry/health counter, persistence/audit adapter, or generic non-session counter.
- Patch any remaining live authority hit discovered by the matrix.
- Provide a concise matrix in the result with file evidence.
- Rerun narrow guard and focused tests; no unclassified residue remains.
