# Implement LogicalFS RO/RW authority boundary end to end

## Problem

Implement the architecture documented in `docs/architecture/logicalfs-realtime-file-authority.md` across the repository. The target boundary is narrow and strict:

- LogicalFS is the only live Cortex/shell `RO` / `RW` file authority.
- Blob remains a cheap byte/object file server for attachments, display bytes, artifact bytes, downloads, and LogicalFS persistence internals.
- Cortex owns scope/workspace semantics but must use LogicalFS for live file operations.
- Sandboxd owns process execution but must not own workspace, subagent, or file persistence semantics.
- Display/download must go through Blob; LogicalFS must not expose display/download handles.

This implementation must avoid the previous failure mode where new code exists but active paths continue to use old logic. Existing user work and historical ledgers must not be reverted.

## Success Criteria

- Repository active shell path uses LogicalFS and sandboxd for Cortex/shell `RO` / `RW` execution, with tests proving the active path.
- No non-LogicalFS live `RO` / `RW` path remains in Cortex, Runtime, or Sandbox code.
- Direct Blob object APIs remain allowed only for cheap byte serving or LogicalFS persistence internals, not live Cortex/shell file semantics.
- Sandboxd service has no Cortex workspace/subagent semantics beyond executing a provided filesystem view.
- Tests/guardrails catch future direct live `RO` / `RW` bypasses.
- Deployment/service scripts include the final service topology and do not reference removed legacy packages or fallback paths.
- Ledger records tickets, results, checks, residual risks, and follow-up closure.
