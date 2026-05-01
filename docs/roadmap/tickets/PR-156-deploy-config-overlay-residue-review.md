# PR-156 — Deploy / Config Overlay Residue Review

| Field | Value |
| --- | --- |
| Status | `[in-progress]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | root deploy scripts, novaic-common, service repos, docs |
| Depends on | PR-155 |

## Goal

Find and remove server overlays, packaged configs, startup scripts, or runtime switches that can silently revive removed old branches or misrepresent the current production path.

## Why This Matters

Deleted code can still be conceptually alive if deployment config, overlays, or packaged resources keep referring to it. Config residue is especially dangerous because it often fails silently.

## Required Process

For this big ticket:

1. Analyze the current live code and deployed behavior.
2. Create small implementation tickets for any concrete cleanup found.
3. Implement each small ticket one by one.
4. Confirm whether config/deploy residue is closed.
5. If not closed, return to step 3; otherwise close this ticket.

## Boundary Invariant

- Runtime switches must describe active product behavior only.
- Removed feature switches must not remain in committed defaults, deploy scripts, packaged resources, or server overlays.
- Startup scripts and Python config loaders must agree.
- Production overlays must fail loud on unknown keys.

## Small Tickets

- [x] [PR-156A — Remove obsolete deploy/start entrypoints](PR-156A-remove-obsolete-deploy-start-entrypoints.md)
- [x] [PR-156B — Remove wake finalizer env branch switches](PR-156B-remove-wake-finalizer-env-switches.md)
- [x] [PR-156C — Add deploy/config overlay guardrail](PR-156C-add-deploy-config-overlay-guardrail.md)

## Current-State Analysis

Active production deployment is the repo-root `./deploy` script plus the server-side
`scripts/start.sh`. `scripts/start.sh` already delegates configuration loading to
`common.strict_config.load_services_config()` and no longer mirrors overlay merge
logic in shell.

Residue found during review:

- Obsolete entrypoints still exist: `scripts/start-all.sh`,
  `scripts/deploy-all.sh`, `scripts/deploy-business.sh`,
  `scripts/gateway/deploy-gateway.sh`, and mirrored copies under
  `scripts/submodules/`.
- Current runbooks still mention `scripts/start-all.sh`,
  `/opt/novaic/jwt_secret.env`, and manual `restart_gw.sh` style flows.
- Runtime still exposes `WAKE_TURN_FINALIZER_ENABLED` and
  `WAKE_TURN_CLOSER_TOOLS`, which can silently alter the current wake finalize
  behavior outside the Cortex scope contract.
- Existing `check_start_config_contract.py` verifies `scripts/start.sh` uses
  `strict_config`, but does not yet ban retired deploy files or retired wake
  switches.

## Unit / Guardrail Tests

- [x] Add tests/guards for any deleted config switch.
- [x] Confirm strict config rejects unknown overlay keys where appropriate.
- [x] Confirm packaged configs do not contain retired switch names.

## Smoke / Deploy

- [ ] Smoke `./deploy status`.
- [x] Smoke affected service restart (`./deploy runtime` for PR-156B).
- [ ] Verify server overlay no longer contains retired keys.

## Git / Merge

- [ ] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark `[deployed]` only after deploy evidence is collected.
