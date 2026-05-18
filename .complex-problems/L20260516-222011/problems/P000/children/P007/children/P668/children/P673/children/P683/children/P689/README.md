# Queue service worker and FSM role map

## Problem

Map queue-service entrypoints and worker roles from source evidence, including queue service API/process, task worker, saga worker, session outbox worker, saga outbox worker, scheduler, health, FSM substrate, and session coordination. Distinguish generic infrastructure from queue-service business/runtime decisions.

## Success Criteria

- Queue-service entrypoint files and launch commands are identified with evidence.
- Worker/FSM roles are summarized in a compact map.
- Any stale/misleading queue-service entrypoint issue discovered is either patched if low-risk or recorded.
- Relevant syntax/import/static checks are run if code changes occur.
