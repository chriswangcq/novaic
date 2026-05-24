# Release Controller

NovAIC release-controller is the long-term CI/CD control plane. It replaces GitHub Actions as the primary release orchestrator, while keeping the existing image-based `deploy` commands as the only backend deployment authority.

## Role

The controller owns release orchestration:

- Poll git branches or accept manual trigger requests.
- Resolve branch rules into a target namespace.
- Run verification commands before building images.
- Build immutable API backend and LLM Factory images.
- Push images to the internal registry.
- Deploy images by calling `./deploy services-image <namespace> <image-ref>` and `./deploy factory-image <namespace> <image-ref>`.
- Record current and previous release pointers.
- Expose health, status, run history, manual trigger, promotion, and rollback APIs.

The controller does not own runtime service discovery, nginx, or application health logic. Service discovery remains the namespace-aware registry. Nginx remains host-level ingress. Backend rollout remains delegated to `deploy`.

## Current Substrate

The API host already has a namespace runtime platform:

| Area | Current path |
| --- | --- |
| API backend deploy | `./deploy services-image <namespace> <image-ref>` |
| LLM Factory deploy | `./deploy factory-image <namespace> <image-ref>` |
| Prod API project | `novaic-prod` |
| Staging API project | `novaic-staging` |
| Prod Factory project | `novaic-llm-factory-prod` |
| Staging Factory project | `novaic-llm-factory-staging` |
| Internal registry bootstrap | `127.0.0.1:5000` |
| Release pointer root | `/opt/novaic/releases` |
| Controller state root | `/opt/novaic/release-controller` |
| Controller Compose package | `/opt/novaic/docker/release-controller` |
| Controller local API | `http://127.0.0.1:19880` |

The release-controller should build on that substrate instead of inventing a parallel deploy mechanism.

## Current Deployment

As of 2026-05-24, the release-controller is deployed on the API host as Docker Compose project `novaic-release-controller`.

```text
container: novaic-release-controller-release_controller-1
image: 127.0.0.1:5000/novaic/release-controller@sha256:9ebe598d9dd8dca0810bc292adc825b6717a3e0041a96d60ea9e95a2e99866e1
bind: 127.0.0.1:19880 -> 19880/tcp
config: /opt/novaic/release-controller/config.json
state: /opt/novaic/release-controller/state
compose: /opt/novaic/docker/release-controller
worktree: /opt/novaic/release-controller/worktree @ 78411ddc0bbf
polling: enabled, dry_run_default=true, interval=60s
executor: Docker CLI + Docker Compose plugin + SSH/rsync inside the controller container, host Docker socket mounted, `/root/.ssh` mounted read-only
```

Health and status checks:

```bash
curl -fsS http://127.0.0.1:19880/health
curl -fsS http://127.0.0.1:19880/v1/status
curl -fsS -X POST http://127.0.0.1:19880/v1/polls/once \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}'
```

The controller has no public Nginx route. Operators should SSH to the API host or use a controlled internal path to call it. Current runtime config keeps `dry_run_default=true`; real non-dry-run branch releases require a managed git worktree at `/opt/novaic/release-controller/worktree` before they should be enabled.

Worktree bootstrap on the API host:

```bash
rm -rf /opt/novaic/release-controller/worktree
git clone git@github.com:chriswangcq/novaic.git /opt/novaic/release-controller/worktree
cd /opt/novaic/release-controller/worktree
git config submodule.novaic-llm-factory.url git@github.com:chriswangcq/novaic-llm-factory.git
git submodule update --init --recursive -- \
  Entangled novaic-agent-runtime novaic-blob-service novaic-business novaic-common \
  novaic-cortex novaic-device novaic-gateway novaic-logicalfs \
  novaic-sandbox-service novaic-llm-factory
```

Autonomous polling is owned by the release-controller process. Enable or pause it by editing `/opt/novaic/release-controller/config.json`, then redeploying the same controller image digest with `./deploy release-controller-image <digest>`.

```json
{
  "polling_enabled": true,
  "dry_run_default": true
}
```

Inspection:

```bash
curl -fsS http://127.0.0.1:19880/v1/status
docker logs --tail 100 novaic-release-controller-release_controller-1
```

Prod remains promotion-only. Branch polling must never resolve to `prod`; `release/*` can create candidates, and `/v1/promotions/prod` requires immutable image refs.

`deploy.verify_commands` must be executable inside the release-controller container. Keep this list to release preflight checks such as `bash -n deploy` and config rendering/compile checks. Full application test suites belong in a builder job/image; the controller then builds immutable service images whose Dockerfiles contain import smoke checks before deployment.

## Branch Rules

Branch rules are explicit configuration. Service names remain unchanged; environment isolation is still namespace-based.

Initial rules:

| Branch pattern | Action | Namespace | Safety |
| --- | --- | --- | --- |
| `main` | verify, build, publish, deploy | `staging` | automatic |
| `preview/*` | verify, build, publish, deploy | `preview-pr-<id>` or configured preview namespace | automatic after rule match |
| `release/*` | verify, build, publish | none by default | produces a promotion candidate |
| manual promote | deploy existing refs | `prod` | explicit API call only |
| manual rollback | deploy previous refs | selected namespace | explicit API call only |

Prod must not deploy directly from branch polling. Prod receives an already-built immutable release pair through a promote command.

## Run Lifecycle

Each release run is a state machine:

```text
queued
  -> planning
  -> verifying
  -> building
  -> publishing
  -> deploying
  -> smoke_testing
  -> succeeded
```

Failure can occur from any active state:

```text
failed
```

A skipped branch head is recorded as:

```text
skipped
```

A run is immutable after it reaches `succeeded`, `failed`, or `skipped`.

## State Model

State is durable JSON on the API host. The controller writes atomically by creating a temp file and renaming it.

```text
/opt/novaic/release-controller/config.json
/opt/novaic/release-controller/state/
  branch-heads.json
  lock.json
  runs/<run-id>.json
  releases/<namespace>-current.json
  releases/<namespace>-previous.json
  candidates/<candidate-id>.json
```

Run record shape:

```json
{
  "run_id": "20260524-113500-main-b3b9d018",
  "trigger": "poll",
  "branch": "main",
  "commit": "b3b9d018...",
  "namespace": "staging",
  "status": "succeeded",
  "api_image": "127.0.0.1:5000/novaic/api-backend@sha256:...",
  "factory_image": "127.0.0.1:5000/novaic/llm-factory@sha256:...",
  "started_at": "2026-05-24T11:35:00+08:00",
  "finished_at": "2026-05-24T11:42:00+08:00",
  "steps": []
}
```

Release pointer shape:

```json
{
  "namespace": "staging",
  "commit": "b3b9d018...",
  "api_image": "127.0.0.1:5000/novaic/api-backend@sha256:...",
  "factory_image": "127.0.0.1:5000/novaic/llm-factory@sha256:...",
  "run_id": "20260524-113500-main-b3b9d018",
  "promoted_from": null,
  "updated_at": "2026-05-24T11:42:00+08:00"
}
```

## Command Boundary

The controller may execute only configured commands. The default command plan is:

```text
git fetch origin <branch>
git checkout --detach <commit>
./scripts/run_all_tests.sh
docker build -f docker/api-backend/Dockerfile -t <api-tag> .
docker build -f docker/llm-factory/Dockerfile -t <factory-tag> novaic-llm-factory
docker push <api-tag>
docker push <factory-tag>
docker inspect -> digest refs
./deploy services-image <namespace> <api-digest>
./deploy factory-image <namespace> <factory-digest>
curl <namespace health URL>
```

The controller records stdout/stderr summaries per step, but should avoid storing secrets.

## API

Initial HTTP API:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | liveness |
| `GET` | `/v1/status` | controller status, lock, current releases |
| `GET` | `/v1/rules` | branch rules |
| `GET` | `/v1/runs` | recent runs |
| `GET` | `/v1/runs/{run_id}` | run details |
| `POST` | `/v1/triggers` | manual non-prod trigger |
| `POST` | `/v1/polls/once` | run one branch-head polling iteration |
| `POST` | `/v1/promotions/prod` | promote existing immutable refs to prod |
| `POST` | `/v1/rollbacks/{namespace}` | redeploy previous namespace refs |

Mutating endpoints require a bearer token from a file or environment variable. Read-only endpoints can be bound to loopback initially.

## Safety Rules

- Branch polling may deploy only non-prod namespaces.
- Prod deployment requires `POST /v1/promotions/prod` with explicit `api_image` and `factory_image`.
- Prod image refs must be digests or accepted immutable sha tags.
- The controller must reject `latest`, `local`, `main`, `master`, `prod`, and `staging` tags for deploy.
- Only one run may execute at a time on the API host.
- A failed run does not update current release pointers.
- Rollback uses the previous release pointer and calls the same image deploy commands.

## Deployment Shape

The controller runs as a Docker service on the API host:

```text
novaic-release-controller
  mounts:
    /var/run/docker.sock
    /opt/novaic/release-controller
    /opt/novaic/releases
    repository checkout/build workspace
```

The Docker socket is powerful. This is acceptable only because the controller is the release authority and runs on the release host. It must not be exposed publicly.

Deploy or update the controller with an immutable image ref:

```bash
./deploy release-controller-image 127.0.0.1:5000/novaic/release-controller@sha256:<digest>
```

Bootstrap note: the first deployed image was built on the API host because the local Docker daemon was unavailable. That is not the durable release path. The durable path is image-based: build elsewhere, push an immutable digest, then run `release-controller-image`.

## Non-goals

- It does not replace the namespace service registry.
- It does not route traffic; nginx remains ingress.
- It does not own application migrations beyond running existing startup/deploy paths.
- It does not make prod automatic from branch polling.
- It does not make GitHub Actions mandatory.
- It does not expose a public release API.

## Migration Plan

1. Implement controller with dry-run and local state.
2. Add Docker package and deploy command.
3. Deploy controller to API host.
4. Verify branch observation and dry-run planning.
5. Enable `main -> staging` polling.
6. Use manual promote for prod.
7. Populate and manage the controller worktree for non-dry-run branch releases.
8. Mark GitHub Actions as secondary verification/fallback path.
