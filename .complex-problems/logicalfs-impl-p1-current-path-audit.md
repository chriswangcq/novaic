# Audit current live RO/RW active paths

## Problem

Before implementing more code, audit the current active paths for Cortex shell
execution, Workspace persistence, LogicalFS, sandboxd, and Blob object use. The
goal is to distinguish already-cut-over paths from old paths that still execute
in production.

## Success Criteria

- Source pointers identify the active shell execution path from tool call to
  LogicalFS and sandboxd.
- Source pointers identify all direct Cortex/Runtime/Sandbox Blob object use
  that could affect live `RO` / `RW`.
- The audit classifies each path as target, transitional, legacy inactive, or
  blocking gap.
- The result becomes the implementation checklist for later child problems.
