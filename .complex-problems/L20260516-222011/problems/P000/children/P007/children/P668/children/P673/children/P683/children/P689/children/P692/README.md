# Queue service launch command evidence supplement

## Problem

Supplement the queue-service role map with explicit launch-command evidence for queue service and queue-service worker roles. Identify where scripts/configs invoke queue service, scheduler, saga/task/outbox workers, or related runtime commands, and update the role-map artifacts without changing production code unless a tiny stale wording issue is discovered.

## Success Criteria

- Exact launch command evidence for queue service and queue-related workers is collected with file/line pointers.
- The queue role-map artifact is updated or supplemented to include launch commands, not only source file roles.
- If no direct launch command exists for a role, that absence is explicitly documented.
- No production code is changed unless a clearly low-risk stale label is found and verified.
