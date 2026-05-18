# PR-183A — Gateway auth token transport tightening

Status: `[closed]` — 2026-05-03

## Finding

`/internal/auth/validate` still advertises a direct `?token=` fallback. The live nginx contract forwards the original parent URI through `X-Original-URI`; direct query token on the internal validation endpoint is not an owned product transport.

## Scope

- Remove the `token` query parameter from `validate_token`.
- Keep `Authorization` and `X-Original-URI` extraction.
- Reword Clerk/internal JWT validation as configured issuer ordering, not fallback.
- Add a source guard for removed direct validate query token path.

## Tests

- Gateway boundary guard.
- Full Gateway suite.

## Deployment / Git

- Deploy Gateway.
- Commit/push `novaic-gateway`.

## Closure

- Removed direct `?token=` query parameter from `/internal/auth/validate`.
- Kept current product transports: `Authorization` header and nginx-forwarded `X-Original-URI`.
- Reworded dual JWT validation as configured issuer ordering instead of fallback.
- Added Gateway boundary guard.
- Tests: `PYTHONPATH=. pytest -q tests/test_pr152_gateway_boundary.py`, `PYTHONPATH=. pytest -q`.
