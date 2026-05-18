# Extracted service entrypoint classification

## Problem

Classify independent service entrypoints for Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, and related service wrappers. Verify whether the repository reflects the intended architecture where foundational file/sandbox services are separate services rather than hidden Cortex internals.

## Success Criteria

- Service entrypoint files and start commands/configs are identified with evidence.
- Each service's current role and dependency boundary is summarized.
- Stale or duplicate service entrypoints that can be safely removed or clarified are handled, otherwise recorded.
- Relevant import/syntax/static checks are run if code changes occur.
