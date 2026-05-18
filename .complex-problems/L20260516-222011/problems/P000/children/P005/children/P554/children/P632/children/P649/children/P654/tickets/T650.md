# Audit and Correct Blob/Workspace Authority Documentation

## Problem Definition

Docs may preserve outdated wording that makes Blob sound like the live Cortex workspace authority. That kind of stale design text is dangerous because future code generation may follow it.

## Proposed Solution

Scan documentation for Blob + Cortex/Workspace/LogicalFS/RO/RW wording, inspect relevant sections, and patch docs that imply Blob owns live workspace semantics. Preserve wording that correctly describes Blob as durable byte/file/artifact storage under LogicalFS or for display/download.

## Acceptance Criteria

- Scan docs/runbooks/architecture files for Blob workspace authority wording.
- Classify findings and patch misleading docs.
- Result cites exact files/sections changed or explains why no patch was needed.
- No code changes unless a doc-driven test/guardrail is required.

## Verification Plan

Run `rg` scans before/after. If docs are patched, run a postscan to verify no high-risk misleading phrase remains.

## Risks

- Docs can mention legacy architecture intentionally; remove or mark as historical rather than silently preserving misleading text.
- Over-editing may erase useful Blob infrastructure details.

## Assumptions

- Correct target wording: Blob stores bytes/artifacts/object payloads; LogicalFS/Workspace own live `/ro` and `/rw` semantics.
