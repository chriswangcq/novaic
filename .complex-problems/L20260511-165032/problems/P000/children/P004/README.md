# Audit Cortex context event source cutover

## Problem

Find any remaining live code paths where Cortex context preparation, stack lifecycle, step recording, or payload reading still use old DFS/source files as authority instead of the event source/projection model, or keep compatibility branches that can silently reintroduce old behavior.

## Success Criteria

- Inspect context event store/projection/read model, API write endpoints, prepare flow, runtime bridge, and old context_stack modules.
- Classify direct DFS file use as authoritative, projection/debug, test-only, or dead residue.
- Record evidence for any live old source-of-truth path.
