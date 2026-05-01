# PR-156 — Deploy / Config Overlay Residue Review

| Field | Value |
| --- | --- |
| Status | `[open]` |
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

- [ ] To be created after current-state analysis.

## Unit / Guardrail Tests

- [ ] Add tests/guards for any deleted config switch.
- [ ] Confirm strict config rejects unknown overlay keys where appropriate.
- [ ] Confirm packaged configs do not contain retired switch names.

## Smoke / Deploy

- [ ] Smoke `./deploy status`.
- [ ] Smoke affected service restart.
- [ ] Verify server overlay no longer contains retired keys.

## Git / Merge

- [ ] Each small ticket can be committed independently where practical.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark `[deployed]` only after deploy evidence is collected.
