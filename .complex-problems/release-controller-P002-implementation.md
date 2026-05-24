# Implement release-controller core service

## Problem

Build the release-controller service that can load config, poll branch heads, plan releases, execute verification/build/publish/deploy commands, persist state, expose status APIs, and support manual trigger/promotion/rollback commands.

## Success Criteria

- Service source exists under a clear repository package.
- Configuration supports branch rules, repo path/URL, registry refs, deploy command paths, poll interval, and dry-run mode.
- State persistence records branch heads, release runs, image refs, current/previous pointers, and failures.
- API exposes health, status, branch rules, runs, trigger, promote, and rollback endpoints.
- Unit tests cover branch mapping, immutable refs, state transitions, and dry-run command planning.

