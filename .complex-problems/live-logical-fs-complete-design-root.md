# Live LogicalFS Complete Design

## Problem

The user wants the most complete RO/RW filesystem solution: not temp projection, not post-run diff/commit, and not command-string based mounting. The target is a live LogicalFS substrate where shell reads/writes are filesystem operations handled by a real component layer.

The solution must preserve the system philosophy:

- Agent is the subject.
- Environment is secondary.
- User is part of the environment.
- Shell sandbox is a tool.
- Business logic should stay small; infrastructure owns infrastructure semantics.
- LogicalFS owns file semantics, not SandboxExec or ShellOrchestrator.

## Success Criteria

- Define the complete target architecture for live LogicalFS.
- Separate responsibilities among LogicalFS, SandboxExec, ShellOrchestrator, Runtime, Blob/OSS, and monitor/observability.
- Explain why commit-based temp projection is not the final model.
- Define live read/write/rename/delete/fsync/journal/blob-sync semantics.
- Define RO/RW/subagent/public/tmp layout under the live filesystem.
- Define crash recovery, durability, consistency, and background sync.
- Define implementation phases, tests, risks, and fallback strategy.
- Do not implement code in this design pass.
