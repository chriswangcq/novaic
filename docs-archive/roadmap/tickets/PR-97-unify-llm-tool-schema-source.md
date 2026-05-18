# PR-97 — Unify LLM tool schema source

| Field | Value |
| --- | --- |
| **Ticket** | PR-97 |
| **Status** | `[✓]` |
| **Scope** | `novaic-common`, `novaic-cortex` |
| **Depends on** | PR-96 |
| **Invariant** | LLM-facing builtin tool schemas have one source of truth. Cortex must not hand-maintain a second copy. |

## Problem

`novaic-cortex` owns the active LLM-facing `BUILTIN_TOOL_SCHEMAS`, while `novaic-common` still carries overlapping tool metadata for `chat_reply`, `sleep`, and `subagent_*` tools. PR-96 had to update both places manually, which proves the schema contract can drift.

## Goal

Move the canonical LLM-facing builtin tool schema data into `novaic-common` and make `novaic-cortex` re-export that source:

- Common owns the canonical `parameters` schema used for LLM calls.
- Cortex imports and exposes the Common schema without duplicating descriptions.
- Legacy Common `inputSchema` tool metadata is adapted from the same canonical source where names overlap.
- Tests fail if Cortex and Common drift.

## Non-Goals

- Do not change the set of LLM-visible builtin tools.
- Do not change tool executor behavior.
- Do not add a new tool registry service.
- Do not revive old Tools Server / MCP hot paths.

## Implementation Checklist

- [x] Add a Common LLM builtin schema module.
- [x] Make Cortex `tool_schemas.py` re-export Common schemas.
- [x] Derive overlapping Common legacy tool metadata from the same source.
- [x] Add drift tests in Common and Cortex.

## Unit / Contract Tests

- [x] Cortex schema tests prove Cortex equals the Common canonical source.
- [x] Common tests prove legacy `inputSchema` adapters are derived from canonical LLM schemas.
- [x] Existing Cortex tool shape/limit tests still pass.

## Smoke Test

- [x] Deploy Cortex with synced Common package.
- [x] Confirm `/v1/internal/tools` returns the same main-agent tool names.
- [x] Confirm deployed source contains no hand-maintained Cortex schema list.

## Deployment Checklist

- [x] Run targeted Common and Cortex tests.
- [x] Deploy `cortex` (syncs `novaic-common` too).
- [x] Verify backend status after deployment.

## GitHub / Commit Checklist

- [x] Commit Common changes.
- [x] Commit Cortex changes.
- [x] Push subrepo branches.
- [x] Bump parent repo submodule pointers / docs and commit.

## Rollback

Revert the Common and Cortex commits. Tool executor behavior is unchanged.
