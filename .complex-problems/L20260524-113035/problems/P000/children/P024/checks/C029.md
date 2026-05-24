# P024 Check: Success after P025

## Judgment

`R024` plus `R025` satisfy `P024`.

## Evidence

- `R024` established the release-controller execution path: Docker CLI, Docker Compose, Docker socket access, build, push, and the real deploy command path.
- `R024` exposed the precise SSH blocker instead of hiding it.
- `P025` fixed that blocker and the subsequent real release blockers:
  - SSH/rsync runtime for deploy commands.
  - Explicit release submodule updates.
  - Published submodule pointers for registry/runtime code.
  - Factory health wait.
  - Staging TLS certificate.
- `R025` proves a full non-dry-run `main -> staging` release succeeded:
  - Run ID `20260524-054536-main-2305e20cc49b`.
  - Commit `2305e20cc49b0fc4cf63adde26810bdf78a100af`.
  - API and Factory images built and pushed.
  - API and Factory staging deployments succeeded.
  - `smoke-staging` succeeded.

## Criteria Map

- Release-controller image contains working `docker` and `docker compose`: satisfied.
- API-host controller container can access the host Docker socket: satisfied.
- Updated image is built, pushed, and deployed by immutable digest: satisfied.
- Non-dry-run `main -> staging` trigger can run verification/build/publish/deploy: satisfied.
- Prod remains promotion-only and cannot be branch-triggered: satisfied by branch rules.
- Docs mention Docker CLI/Compose runtime dependency: satisfied in `docs/architecture/release-controller.md` and `docs/runbooks/deploy.md`.

## Residual Risk

Automatic polling still uses `dry_run_default=true`. This is deliberate operating policy after proving manual non-dry-run execution; flipping it to false is a separate production-risk decision, not a P024 correctness gap.
