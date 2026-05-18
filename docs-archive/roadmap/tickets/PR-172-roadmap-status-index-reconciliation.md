# PR-172 — Roadmap Status Index Reconciliation

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | docs |
| Depends on | PR-169, PR-170, PR-171 |
| Theme | Documentation entropy cleanup |

## Goal

Make the ticket index match the actual closed state of PR-169, PR-170, and PR-171.

## Current-State Analysis

The individual ticket files are closed, but `docs/roadmap/tickets/README.md` still lists PR-169, PR-170, and PR-171 as `[open]`. This creates a false gap and can send future work back into already-closed branches.

## Implementation

- Update the ticket index rows to `[closed]`.
- Replace "Big ticket" notes with closure summaries.

## Tests / Smoke

- Static grep that PR-169/170/171 are no longer marked `[open]` in the ticket index.

## Closure

- PR-169/170/171 ticket index rows now match their closed ticket files.
- No service deploy required.

## Deploy / GitHub

- No service deploy required.
- Commit docs in the parent repo.
