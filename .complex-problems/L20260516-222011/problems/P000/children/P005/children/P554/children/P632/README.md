# LogicalFS Sandbox Fallback Remediation Guard

## Problem

After removing stale materialization/scratch residue, the codebase needs a final skeptical guard pass so future changes do not reintroduce local materialization, old sandbox temp paths, Blob-as-workspace semantics, or runtime-local shell fallback.

## Success Criteria

- Runs targeted static scans for `materialize`, `novaic-cortex-sandbox`, `/tmp/novaic-cortex-sandbox`, `/rw/scratch`, local shell fallback, and direct Blob workspace authority terms.
- Runs focused Cortex LogicalFS/workspace/sandbox boundary tests.
- Documents any remaining hits as intended, removed, or follow-up-worthy.
- Creates a follow-up if any risky active residue remains.
