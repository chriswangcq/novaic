# Worker and service entrypoint topology inventory

## Problem

Inventory backend worker/service entrypoints from source code and package/config metadata. Build a code-evidence-based map of task, saga, outbox, scheduler, health, queue, Cortex, sandbox, LogicalFS, and Blob service roles without relying on memory.

## Success Criteria

- Worker/service entrypoint files and launch commands are located from source/config.
- Current roles are summarized with file evidence.
- Stale or duplicate entrypoint code that is safe to remove/update is handled or recorded.
- Relevant import/syntax or focused tests are run where changes occur.
