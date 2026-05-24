# Roll out controller-only deployment and clean release documentation

## Problem

The code change can temporarily break staging polling if the guarded `deploy` script reaches the API host before the running controller image knows how to pass controller env vars. Documentation also still presents manual deployment commands as acceptable release paths. This child exists to migrate in the right order and verify the final platform shape.

## Success Criteria

- Release Controller runtime is upgraded to code that passes deploy identity before guarded deployments are exercised.
- Staging release and prod promotion/rollback flow are verified through Release Controller APIs or polling.
- Docs describe Release Controller as the only backend/factory release interface and `deploy` as internal executor.
- Manual backend deploy paths are audited after deployment and fail locally before remote side effects.
