# Agent runtime loop and worker role map

## Problem

Map agent-runtime entrypoints from source evidence, including runtime loop, shell/tool execution boundaries, queue worker integration, and any runtime process wrappers. Explain how runtime processes relate to queue-service workers without conflating CPU/process with ledger/outbox state.

## Success Criteria

- Agent-runtime entrypoint files and launch commands are identified with evidence.
- Runtime loop/tool execution roles are summarized in a compact map.
- Misleading or stale runtime entrypoint naming is patched if low-risk or recorded.
- Relevant syntax/import/static checks are run if code changes occur.
