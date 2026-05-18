# Queue and runtime worker role classification

## Problem

Classify queue-service and agent-runtime worker entrypoints from source evidence: task worker, saga worker, session outbox worker, saga outbox worker, scheduler, health, queue service, and runtime loop entrypoints. Explain which are generic worker infrastructure versus business/runtime-specific computation.

## Success Criteria

- Queue/runtime entrypoint files and launch commands are identified with file evidence.
- Worker roles are summarized clearly without relying on old mental models.
- Misleading duplicate or stale queue/runtime entrypoint code is patched if low-risk, otherwise recorded as residual risk.
- Relevant syntax/import/static checks are run if code changes occur.
