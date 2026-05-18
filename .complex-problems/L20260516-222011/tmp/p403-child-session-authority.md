# Runtime session authority residue cleanup

## Problem

Runtime session-authority files (`session_repo`, `session_fsm`, `session_outbox`, `session_recovery`, `session_ledger`, `session_observed_events`, `queue_audit`) contain active/finalize/restart/archive generation-related hits. They must be classified or patched so live session mutation never accepts missing/stale/implicit generation.

## Success Criteria

- Inspect all session-authority runtime hits from the P402 guard outputs.
- Patch any live missing/stale/implicit generation compatibility residue.
- Classify safe validators, audit readers, and explicit projections with file evidence.
- Add focused tests for changed live session authority paths.
- Rerun session-authority runtime guards and focused tests.
