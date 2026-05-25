# Release Controller deploy result

## Summary

Release Controller deployed the fixed commit to staging and promoted the same immutable images to prod.

## Done

- Staging run `20260525-003420-main-83fe6bb4bc20` succeeded.
- Prod promotion run `20260525-003822-promote-prod-staging-83fe6bb4bc20` succeeded.
- Current Release Controller pointers for both staging and prod now reference commit `83fe6bb4bc20a0af96674fd71ea2d9b97e058059`.
- Both staging and prod use:
  - API backend: `127.0.0.1:5000/novaic/api-backend:sha-83fe6bb4bc20`
  - LLM Factory: `127.0.0.1:5000/novaic/llm-factory:sha-83fe6bb4bc20`

## Verification

- `/v1/runs/20260525-003420-main-83fe6bb4bc20`: `status=succeeded`, `execution.succeeded=true`.
- `/v1/runs/20260525-003822-promote-prod-staging-83fe6bb4bc20`: `status=succeeded`, `execution.succeeded=true`.
- `docker ps` shows prod and staging backend services running `sha-83fe6bb4bc20`.
- `https://staging-api.gradievo.com/api/health`, `https://api.gradievo.com/health`, and `http://127.0.0.1:19999/api/health` returned healthy JSON.

## Known Gaps

- Production message recovery still needs P006 verification at the subscriber/Entangled/Queue boundary.
- Final ledger closure still needs a ledger-only commit after verification.

## Artifacts

- Release Controller staging run: `20260525-003420-main-83fe6bb4bc20`
- Release Controller prod promotion run: `20260525-003822-promote-prod-staging-83fe6bb4bc20`
