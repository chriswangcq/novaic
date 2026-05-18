# Active stack source and projection map

## Problem

Active skill stack state is produced by Cortex lifecycle APIs and stored/projected through operational state. Before judging final LLM ordering, the source of truth must be mapped: where frames are written, read, finalized, and how stale file-walk or duplicate stack sources are avoided.

## Success Criteria

- Identify the active stack source of truth and all production write/read/finalize call sites.
- Document whether active stack state is SQLite/operational-store backed or file-walk backed.
- Run focused Cortex tests covering active stack projection, lifecycle APIs, and source guardrails.
- Fix or split any stale source path that can bypass the active stack projection.
