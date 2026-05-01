# PR-153A — Remove Subscriber Switch Residue

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-153 |
| Repos | novaic-business, scripts, docs |

## Goal

Remove stale `subscriber_enabled` / disabled-subscriber wording from active subscriber code comments and tighten guardrails so the required subscriber process cannot be mistaken for an optional canary branch.

## Why This Matters

The product loop is now subscriber-owned. Any active comment, deployment note, or lint gap that still suggests an on/off subscriber branch can mislead future changes into rebuilding the old dual-loop design.

## Implementation Plan

1. [x] Remove active `subscriber_enabled` references from `main_subscriber.py` and deployment comments.
2. [x] Keep historical archaeology only where explicitly archived, not in current operational docs.
3. [x] Extend `scripts/ci/lint_agent_loop_path.sh` so active subscriber files are scanned.

## Unit / Guardrail Tests

- [x] `scripts/ci/lint_agent_loop_path.sh` passes.
- [x] Targeted subscriber tests pass: `python3 -m pytest tests/test_dispatch_subscriber.py -q` — 23 passed.

## Smoke / Deploy / Git

- [ ] Smoke subscriber process starts as required under `./deploy gateway`.
- [ ] Deploy affected services if code changes are made.
- [x] Commit affected repos: `novaic-business` `661945d business: remove subscriber switch residue`.
- [ ] Parent repo submodule/docs commit and push.
