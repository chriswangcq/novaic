# Subagent finalize status identity aggregate verification

## Problem

After payload, handler, and ordering changes land, P354 needs an aggregate check that the terminal subagent status path no longer has stale finalize or compatibility residue.

## Success Criteria

- Run focused tests covering wake_finalize payloads, subagent handlers, task path contracts, finalize ownership, and saga DAG integration.
- Run source guards for `last_scope_id`, generation defaulting, and missing-generation compatibility in the touched runtime files.
- Verify there is no direct Business status mutation path from finalize tasks that bypasses the new identity contract.
- Record residual risks explicitly, especially recovery/compensation paths delegated to P351.
