# Runtime finalize enforcement aggregate verification

## Problem

After P337 implementation children complete, run an aggregate verification that stale/missing runtime finalize identity cannot mutate Cortex, session state, or pending inbox, while valid finalize still works.

## Success Criteria

- Run focused tests across react contracts, cortex handlers, session-ended delivery, repository finalize, recovery/compensation, and pending restart.
- Run source guards for `session_generation or 0` in finalize-producing runtime paths.
- Record residual risks and follow-ups if any mutation path remains only partially guarded.
