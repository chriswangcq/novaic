# Live LogicalFS Complete Design Check

## Summary

Success. The design defines the complete target architecture: a live LogicalFS substrate owns filesystem semantics, SandboxExec is only a process runner, ShellOrchestrator only coordinates lifecycle, and Blob/OSS remains the durable object backend.

## Evidence

- R000 defines component boundaries and final mental model.
- R000 explicitly removes `commit` from Sandbox/ShellOrchestrator semantics.
- R000 defines live read/write/rename/delete/tmp/journal/blob-sync semantics.
- R000 defines RW layout and subagent/public/tmp conventions.
- R000 defines crash recovery, sync queue, metadata model, observability, security/identity, phases, tests, and non-goals.
- R000 maps the design to current code points that must be replaced or demoted.

## Criteria Map

- Complete target architecture -> R000 sections 1-6.
- Responsibility separation -> R000 sections 1-2.
- Why commit-based temp projection is not final -> R000 section 3.
- Live operation semantics -> R000 sections 7-10.
- RO/RW/subagent/public/tmp layout -> R000 section 11.
- Crash recovery, durability, consistency, background sync -> R000 sections 8, 13, 14.
- Implementation phases, tests, risks, fallback -> R000 sections 17-19 plus Known Gaps.
- No implementation -> R000 verification says design only.

## Execution Map

- T000 -> R000: complete live LogicalFS design pass.

## Stress Test

- Failure mode: Sandbox accidentally owns file semantics. Result: R000 makes SandboxExec a pure process runner.
- Failure mode: Orchestrator grows a commit path. Result: R000 makes release_view ref cleanup only, not commit.
- Failure mode: Blob is treated as a filesystem. Result: R000 keeps Blob as object backend and LogicalFS as filesystem provider.
- Failure mode: live writes are lost before Blob sync. Result: R000 adds local WAL/journal, dirty sync state, recovery, and retry queue.
- Failure mode: FUSE complexity is hidden. Result: R000 calls it the complete target while preserving staged implementation and fallback.

## Residual Risk

- Non-blocking: FUSE-backed live FS is a major infrastructure project and requires staged migration, metrics, and fallback.
- Non-blocking: distributed multi-writer conflict resolution is intentionally out of scope.

## Result IDs

- R000

## Blocking Gaps

- none
