# PR-171 — Final Old Path Physical Deletion and Guardrails

| Field | Value |
| --- | --- |
| Status | `[open]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Repos | all first-party repos |
| Depends on | PR-167, PR-168, PR-169, PR-170 |
| Theme | Entropy cleanup |

## Goal

After the new Environment → Cortex → Activity Timeline path is live, physically delete remaining old compatibility branches and add guardrails that make old paths fail fast.

## Current-State Analysis

Most old communication tools and raw log payload paths are gone. Remaining transitional residues include message-backed Environment notification mapping, App monitor execution-log bridge behavior, trace projection recognition of old `chat_reply`, and historical test fixtures that still encode retired names for compatibility checks.

## Small Tickets

- PR-171A — Remove message-backed Environment notification compatibility.
- PR-171B — Remove App execution-log user monitor fallback.
- PR-171C — Remove retired tool-name aliases from Cortex/App projection except archived tests.
- PR-171D — Repo-wide guardrails for raw unobserved prompt content, raw payload Cortex writes, and old communication tools.

## Done Criteria

- No active code has “new path or old path” branching.
- Tests fail if old communication, summary, or raw diagnostic paths return.
- Historical docs remain clearly archived and cannot be mistaken for current runbooks.
