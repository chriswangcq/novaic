# LogicalFS Snapshot Patch Versus Live Filesystem

## Problem

Shell uses a materialized LogicalFS snapshot and writes RW changes back on release. This is clean enough for current shell execution, but not a fully live realtime LogicalFS service.

## Success Criteria

- Decide whether snapshot/patch is the final model or a phase before live LogicalFS.
- If live LogicalFS is desired, define how SQLite/LogicalFS metadata and Blob bytes participate.
- Include correctness rules for crash recovery, concurrent subagents, and no explicit commit.
