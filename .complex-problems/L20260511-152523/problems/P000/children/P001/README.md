# Live production stall diagnosis

## Problem

Determine the exact production stuck state after one agent loop. Inspect live process status, runtime/Cortex logs, queue database rows, and worker health without modifying production data. Produce a concrete root-cause hypothesis tied to evidence.

## Success Criteria

- Remote process and worker status are checked.
- Recent logs are inspected with timestamps, distinguishing stale errors from current failures.
- Queue database state is inspected for active sessions, pending inbox/outbox, saga rows, session states, and retry/dead rows.
- The failing or waiting state is identified precisely enough to guide a code fix.
