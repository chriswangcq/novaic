# Cortex API materialization call-site map

## Problem

Cortex API endpoints may append ContextEvents and also materialize debug projections into workspace files. These call sites must be mapped so event authority and projection materialization remain intentionally paired.

## Success Criteria

- API call sites for context message writes, batch writes, tool step writes, and payload reads are mapped with source pointers.
- Each call site is classified as authoritative event append, materialized projection write, explicit payload retrieval, or legacy/stale path.
- Tests covering API context writes and step writes are identified and run.
- Any duplicate active write path that can diverge from ContextEvents is fixed or split.
