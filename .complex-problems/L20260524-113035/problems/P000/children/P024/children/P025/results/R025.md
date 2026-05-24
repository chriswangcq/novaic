# T025 Result: Deploy fixed controller and verify staging release

## Summary

Deployed the SSH-capable release-controller, fixed the release worktree submodule update path, restored staging from the bad image caused by stale submodule pointers, fixed the Factory health gate, issued the missing staging TLS certificate, and proved a full non-dry-run `main -> staging` release through the controller.

## Source Changes Published

- Submodule commits pushed:
  - `novaic-common@03174b5f5778`: namespace-aware service registry/runtime source.
  - `novaic-agent-runtime@fd88323dd1c5`: removed sqlite runtime dependency residue.
  - `novaic-business@8c2a69cb75d9`: require configured LLM Factory URL.
  - `novaic-llm-factory@23b77feef189`: align Factory default port.
- Main commits pushed:
  - `2b71adfc`: published release-controller executor dependencies and submodule pointers.
  - `73a8b6a6`: added submodule update steps to release planning.
  - `41a387bc`: limited release submodule update to explicit release-relevant submodules.
  - `2305e20c`: added bounded Factory health wait during image deploy.

## Controller Deployment

- Deployed release-controller image digest:
  - `127.0.0.1:5000/novaic/release-controller@sha256:4440870984db615a714d5299103a61f1232fa76b1c8c2edd52e64c285433285e`
- Running controller capability checks passed:
  - `docker --version`: Docker 29.1.3.
  - `docker compose version`: Docker Compose v2.40.3.
  - `ssh -o BatchMode=yes root@api.gradievo.com true`: passed from inside the controller container.
  - `rsync --version`: rsync 3.4.1.
  - Host Docker socket access works.
- Runtime config now explicitly declares release-relevant submodules:
  - `Entangled`
  - `novaic-agent-runtime`
  - `novaic-blob-service`
  - `novaic-business`
  - `novaic-common`
  - `novaic-cortex`
  - `novaic-device`
  - `novaic-gateway`
  - `novaic-llm-factory`
  - `novaic-logicalfs`
  - `novaic-sandbox-service`

## Runtime Fixes Applied

- API-host root SSH was made usable for controller batch deploy commands by ensuring `/root/.ssh` has a usable key, `authorized_keys`, and `known_hosts`.
- `staging-api.gradievo.com` had DNS but used the `api.gradievo.com` certificate. Issued a dedicated Let's Encrypt certificate and updated Nginx to use:
  - `/etc/letsencrypt/live/staging-api.gradievo.com/fullchain.pem`
  - `/etc/letsencrypt/live/staging-api.gradievo.com/privkey.pem`

## Successful Release Evidence

Controller run:

- Run ID: `20260524-054536-main-2305e20cc49b`
- Commit: `2305e20cc49b0fc4cf63adde26810bdf78a100af`
- Namespace: `staging`
- Dry run: `false`
- Status: `succeeded`
- Failed step: none

Successful steps:

- `git-fetch`
- `git-checkout`
- `git-submodule-sync`
- `git-submodule-update`
- `verify-1`
- `verify-2`
- `build-api-backend`
- `build-llm-factory`
- `push-api-backend`
- `push-llm-factory`
- `deploy-api-staging`
- `deploy-factory-staging`
- `smoke-staging`

Final staging images:

- `novaic-staging-service-registry-1`: `127.0.0.1:5000/novaic/api-backend:sha-2305e20cc49b`, healthy.
- `novaic-staging-gateway-1`: `127.0.0.1:5000/novaic/api-backend:sha-2305e20cc49b`, healthy.
- `novaic-staging-business-1`: `127.0.0.1:5000/novaic/api-backend:sha-2305e20cc49b`, healthy.
- `novaic-llm-factory-staging-llm-factory-1`: `127.0.0.1:5000/novaic/llm-factory:sha-2305e20cc49b`, healthy.

Health checks:

- `http://127.0.0.1:29999/api/health`: 200.
- `http://127.0.0.1:29990/health`: 200.
- `https://staging-api.gradievo.com/api/health`: 200 with a valid `staging-api.gradievo.com` certificate.
- `http://127.0.0.1:19880/health`: 200.

## Prod Safety

Runtime branch rules remain:

- `main -> staging` auto-deploy.
- `preview/* -> preview-{slug}` auto-deploy.
- `release/* -> candidate_only`.

There is no branch rule targeting `prod`; production remains promotion-only.

## Result

T025 is complete: the centered release-controller can execute a real staging release from branch head through build, push, deploy, and smoke. The remaining policy switch is separate: `dry_run_default` is still `true`, so polling observes and records by default; manual non-dry-run execution has been proven.
