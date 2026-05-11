# Audit Queue FSM Saga and session adapter cutover

## Problem

Find any remaining live code paths in agent runtime where queue dispatch/session/saga/outbox still bypass the intended FSM/outbox/generation-checked model, use old active-session pointers as authority, or contain fallback/direct imperative branches that can keep old behavior live.

## Success Criteria

- Search and inspect queue service, session state/repo, dispatch subscriber/client, saga orchestrator/repo, outbox workers, and worker assembly.
- Identify confirmed live bypasses vs transitional views/caches.
- Check for hidden env/time/id dependencies in core decision paths where relevant.
- Record evidence and prioritized findings.
