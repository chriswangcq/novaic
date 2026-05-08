# Code repair queue dispatch and saga claim

## Problem

Patch the runtime/common code so Business subscriber dispatch does not use the default 5s httpx timeout and Queue Service saga claim/FSM event writes do not fail with `sqlite3.OperationalError: database is locked` under normal concurrent worker polling.

## Success Criteria

- Relevant code paths are identified and patched.
- Patch is scoped to dispatch timeout and queue-service SQLite/FSM claim reliability.
- No old bypass branch is introduced.

