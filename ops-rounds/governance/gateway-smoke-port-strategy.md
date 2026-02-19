# Gateway Smoke Port Strategy (Stable Policy)

## Purpose
Define a reproducible and low-flake port strategy for gateway independent startup smoke checks.

## Scope
- script: `novaic-backend/scripts/smoke_gateway_independent_startup.sh`
- CI job: `.github/workflows/ci.yml` job `gateway-smoke`

## Canonical Strategy
- Use deterministic fallback base ports:
  - `61900`
  - `62000`
  - `62100`
- For each base, derive service ports by fixed offsets:
  - runtime-orchestrator: `base + 93`
  - gateway: `base + 99`
  - queue-service (dependency URL placeholder): `base + 97`
  - tools-server (dependency URL placeholder): `base + 98`
  - vmcontrol (dependency URL placeholder): `base + 96`
  - file-service (dependency URL placeholder): `base + 95`
  - tool-result-service (dependency URL placeholder): `base + 94`

## Retry and Fallback Rule
- Smoke script must attempt bases in order (`61900 -> 62000 -> 62100`).
- A base attempt fails only when health checks do not become ready in bounded retries.
- On failure, process cleanup is mandatory before trying next base.

## Validation Rule
- Success criteria for each replay:
  - runtime-orchestrator `/api/health` is reachable
  - gateway `/api/health` is reachable
  - gateway `/api` root is reachable
- The script output must include:
  - `PASS: startup smoke base <base>`
  - `PASS: runtime-orchestrator healthy on <port>`
  - `PASS: gateway healthy on <port>`
  - `PASS: gateway API root reachable`

## Audit Notes
- This policy is stable and must not rely on round-only reports.
- Round reports may attach replay output as evidence, but policy source of truth stays here.
