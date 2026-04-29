# PR-101 — Config reading contract guardrails

| Field | Value |
| --- | --- |
| **Ticket** | PR-101 |
| **Status** | `[✓]` |
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

- [x] Add test or script guard for config overlay parity.
- [x] Update docs/comments if stale.
- [x] Run config/deploy guard tests.
- [x] No deployment required unless script behavior changes.
- [x] Commit, push, and bump parent repo.

## Verification

- `bash -n scripts/start.sh`
- `python3 scripts/ci/check_start_config_contract.py`
- `cd novaic-common && python -m pytest tests/test_strict_config_runtime_switches_overlay.py tests/test_service_config_runtime_switches.py tests/test_strict_config.py`
- `./deploy runtime`
- `./deploy status`
- Remote smoke: `/opt/novaic/start.sh` imports `common.strict_config.load_services_config` and contains the no-reimplementation guard comment.
