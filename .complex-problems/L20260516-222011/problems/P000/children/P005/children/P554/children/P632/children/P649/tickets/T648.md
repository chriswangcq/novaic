# Audit Blob Workspace Authority Residue

## Problem Definition

Blob should be a cheap artifact/file service, while live Cortex workspace semantics should be owned by LogicalFS/Workspace. The repo may still contain docs, tests, or runtime paths implying Blob is the authority for live `/ro`/`/rw` workspace state.

## Proposed Solution

Search Cortex/runtime/common/docs for Blob workspace authority terms, inspect live code paths around matches, classify each category, and remove or spawn follow-up for active residue. Do not rewrite valid artifact/display/download Blob usage.

## Acceptance Criteria

- A focused scan covers terms such as `blob`, `Blob`, `WorkspaceRegistry`, `workspace`, `artifact`, `/ro`, `/rw`, and authority/semantic wording in Cortex/runtime/common/docs.
- Remaining hits are classified as valid artifact/file-service use, historical docs/tests, or active bad authority path.
- Any active bad authority path is fixed or converted into a child/follow-up problem.
- Evidence is recorded with scan files and pointers.

## Verification Plan

Run `rg` scans, inspect high-risk files (`novaic-cortex` registry/workspace/context paths, `novaic-logicalfs`, `novaic-sandbox-service`, `docs/*blob*`, `docs/cortex*`), and run targeted tests if code changes are needed.

## Risks

- Blob appears in many legitimate artifact paths; over-cleaning could break display/download behavior.
- Docs may intentionally describe Blob as durable backing storage, which is valid only when separated from live workspace authority.

## Assumptions

- Blob may store durable bytes/artifacts, but Cortex live semantic state must not be controlled through ad hoc Blob APIs that bypass Workspace/LogicalFS contracts.
