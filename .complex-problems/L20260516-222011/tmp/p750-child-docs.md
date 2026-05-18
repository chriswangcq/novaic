# Active Docs Boundary Wording Remediation

## Problem

Patch active architecture/docs wording that overstates ownership or mixes semantic authority with file-operation substrate authority.

## Success Criteria

- `docs/architecture/logicalfs-realtime-file-authority.md` distinguishes Cortex semantic ownership from LogicalFS file-operation/view authority.
- `docs/architecture/cortex.md` and `docs/cortex-architecture.md` describe Cortex as orchestrating shell/workspace semantics while delegating process execution to Sandboxd and file operations to LogicalFS.
- `docs/architecture/data-ownership.md` clearly separates Cortex scope/context/workspace semantics, LogicalFS live RO/RW operations/view contract, and Blob byte/object ownership.
- Changes are wording-only and do not introduce new architecture claims not supported by code.

