# Enforce Release Controller-only backend deploy entrypoints in code

## Problem

Release Controller plans and the `deploy` executor do not yet share a hard invocation contract. Direct manual backend and Factory deployment targets are still visible and callable, while the controller does not identify its deploy calls with a run id and namespace. This child exists to make the code and tests enforce controller-only release mutation.

## Success Criteria

- Planner adds controller identity env vars to backend and Factory deploy steps.
- Runner merges step env with the existing environment.
- `deploy` fails fast for direct backend/factory image deployment without controller env metadata.
- Obsolete backend remote-build/legacy deployment targets fail as disabled manual paths.
- Unit/CI tests cover env injection, env merging, and manual path rejection.
