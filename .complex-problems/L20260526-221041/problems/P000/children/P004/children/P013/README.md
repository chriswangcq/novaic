# Review streaming contracts and remove misleading residue

## Problem

The code should express one clean long-term path: Factory streaming chunks, Runtime aggregation/projection, Entangled activity records, and App Timeline rendering. The diff/source must not leave long-lived fallback branches, stale misleading paths, or raw partial reasoning accidentally added into future LLM input history.

## Success Criteria

- Source review finds no long-term fallback branch for the new reasoning streaming path.
- Runtime aggregation returns a final assistant response while activity projection uses streaming deltas without injecting partial reasoning into the next LLM input history.
- App path review confirms no parallel reasoning transport and no stale monitor path left by this work.
- Any cleanup needed is implemented and covered by focused tests or explicit evidence.
