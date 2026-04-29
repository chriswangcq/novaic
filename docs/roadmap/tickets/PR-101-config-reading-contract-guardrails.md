# PR-101 — Config reading contract guardrails

| Field | Value |
| --- | --- |
| **Ticket** | PR-101 |
| **Status** | `[ ]` |
| **Scope** | `novaic-common`, `scripts`, optional App resources |
| **Depends on** | PR-100 |
| **Invariant** | Python services and deployment scripts must resolve `services.json` + runtime-switch overlays the same way. |

## Problem

`common.strict_config` is the Python config loader, but `scripts/start.sh` carries a shell/Python `_cfg` reader that independently mirrors overlay semantics. App resources also ship config copies. Drift here can make deployment and service runtime disagree.

## Goal

- Add guardrails that prove `start.sh` overlay resolution matches `common.strict_config`.
- Document the canonical runtime-switch overlay flow.
- Keep production overlay separate from rsync-stomped defaults.

## Non-Goals

- Do not move all deployment logic into Python in this ticket.
- Do not change production secrets or overlay values.
- Do not alter service ports.

## Checklist

- [ ] Add test or script guard for config overlay parity.
- [ ] Update docs/comments if stale.
- [ ] Run config/deploy guard tests.
- [ ] No deployment required unless script behavior changes.
- [ ] Commit, push, and bump parent repo.

