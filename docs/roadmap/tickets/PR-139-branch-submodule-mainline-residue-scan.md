# PR-139 — Branch and Submodule Mainline Residue Scan

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | parent repo plus all tracked submodules |
| Depends on | PR-138 |

## Goal

Eliminate misleading branch/submodule state: every actively maintained repo should either be on `main` or have an explicit reason not to be. No hidden work branch should look like a production path.

## Scan Plan

1. [x] Check root and submodule working tree status.
2. [x] Check current branch for every tracked submodule.
3. [x] Check whether obsolete `codex/*` branches remain locally or remotely.
4. [x] Check whether root submodule pointers match the expected deployed commits.

## Findings

- Root repo is on `main`.
- All tracked first-party submodules are on `main`: `novaic-agent-runtime`, `novaic-app`, `novaic-business`, `novaic-common`, `novaic-cortex`, `novaic-device`, `novaic-gateway`, `novaic-llm-factory`, `novaic-mcp-vmuse`, `novaic-quic-service`, `novaic-storage-a`, plus `Entangled` and website repos.
- Root working tree only contains the newly created scan-ticket docs and roadmap index edits.
- No first-party repo has local or remote `codex/*` branches left.
- `thirdparty/openclaw` still has upstream `origin/codex/*` branches. This is an external upstream repo, not a Novaic production branch residue.
- Some submodule status lines include `git describe` style version suffixes, but direct branch checks confirm they are on `main`.

## Follow-up Decision

No first-party branch cleanup is needed. Keep this ticket as the scan record; do not act on OpenClaw upstream branches.

## Unit / Guardrail Tests

- [x] No new guardrail added; the scan did not find first-party branch drift.

## Smoke / Deploy

- [x] No deploy for scan-only changes.
- [x] No cleanup follow-up required from this ticket.

## Git / Merge

- [x] Commit ticket updates.
- [x] Push parent docs update.

## Closure — 2026-05-01

PR-139 is closed as a scan-only ticket. No first-party branch drift was found, and the parent docs update was committed and pushed as part of the cleanup closure.
