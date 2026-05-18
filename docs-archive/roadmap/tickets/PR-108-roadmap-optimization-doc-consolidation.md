# PR-108 — Consolidate backend optimization roadmap documents

| Field | Value |
| --- | --- |
| **Ticket** | PR-108 |
| **Status** | `[✓]` |
| **Scope** | `docs` |
| **Depends on** | PR-106, PR-107 |
| **Invariant** | Backend architecture optimization and LLM-call contract backlog should have one roadmap entry point. |

## Problem

The backend optimization recommendations and LLM-call contract backlog lived in separate documents, which made the roadmap look split even though both describe the same maintenance objective: keep Cortex/Runtime structure small, explicit, and testable.

## Design

- Merge the LLM-call contract backlog into `backend-architecture-optimization-recommendations.md`.
- Delete the standalone `llm-call-contract-feature-backlog.md`.
- Replace outdated root-scope-finalizer wording with the current wake-scope closure summary contract.
- Keep current rough edges in the same roadmap document.

## Implementation Checklist

- [x] Add an `LLM Call Contract Backlog` section to the backend optimization roadmap.
- [x] Delete `docs/roadmap/llm-call-contract-feature-backlog.md`.
- [x] Merge the mDNS policy and WebRTC runtime smoke items into one rough-edge item.
- [x] Ensure no docs reference the deleted file.

## Unit Test / Static Check Work

- [x] Run `git diff --check` for touched docs.
- [x] Run `rg` to confirm no live references to the deleted standalone backlog remain.

## Smoke Test Work

- [x] Open/read the merged roadmap section and verify it is coherent as a single entry point.

## Deployment Work

- [x] No runtime deploy required; docs-only.

## GitHub / Commit Work

- [x] Commit docs and ticket changes in the parent repo.

## Closeout

Completed locally on 2026-04-30.

Verification:

- `git diff --check -- docs/roadmap/backend-architecture-optimization-recommendations.md docs/roadmap/llm-call-contract-feature-backlog.md docs/roadmap/tickets/PR-106-host-desktop-device-status-closure.md docs/roadmap/tickets/PR-107-vmcontrol-webrtc-mdns-closure.md docs/roadmap/tickets/PR-108-roadmap-optimization-doc-consolidation.md docs/roadmap/tickets/README.md`
- `rg -n "llm-call-contract-feature-backlog|LLM Call Contract Feature Backlog|Root-scope continuity finalizer" docs/roadmap -g "*.md" -g "!docs/roadmap/tickets/PR-108-roadmap-optimization-doc-consolidation.md"`
