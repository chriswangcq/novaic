# Side-effect bypass final guard

## Problem

Run a final source guard across session/queue/task code for direct side-effect bypasses and produce a final classification.

## Success Criteria

- Save guard artifacts for direct saga creation, queue publish, session attach input, Cortex scope end, and session outbox usage.
- Confirm no dangerous live bypass remains.
- Route any unclassified hit into a follow-up.
