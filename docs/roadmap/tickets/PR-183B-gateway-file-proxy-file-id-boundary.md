# PR-183B — Gateway file proxy file-id boundary

Status: `[closed]` — 2026-05-03

## Finding

Gateway previously exposed product-file proxy routes that mixed ownership
checks, storage resolution, and raw object access. Those routes have since been
replaced by the Blob proxy boundary.

## Scope

- Reject raw storage-path access at Gateway.
- Preserve only auth-bound Blob proxy behavior.
- Pass user identity explicitly when Gateway calls Blob Service so the storage
  owner boundary is not implicit.
- Add source/route guard.

## Tests

- Gateway file proxy source guard.
- Full Gateway suite.

## Deployment / Git

- Deploy Gateway.
- Commit/push `novaic-gateway`.

## Closure

- Raw storage-path bypasses return 404.
- Gateway passes user identity explicitly to Blob Service.
- Active product file access now goes through Blob proxy semantics.
- Added Gateway boundary guard.
- Tests: `PYTHONPATH=. pytest -q tests/test_pr152_gateway_boundary.py`, `PYTHONPATH=. pytest -q`.
