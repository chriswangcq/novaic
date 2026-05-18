# Run Business focused tests and final active residue scan

## Problem
After Business residue cleanup, the code needs proof: focused tests plus a final scan with explicit classification for any remaining terms.

## Success Criteria
- Focused Business tests pass for dispatch subscriber, subagent spawn/state, environment internal API, assembler factory, schema/entity paths as applicable.
- Final active residue scan is run.
- Every remaining scan hit is listed as either removed, current shell boundary, current minimal adapter, or test-only/non-active.
