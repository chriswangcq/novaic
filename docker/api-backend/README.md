# NovAIC API Backend Image

This package contains the shared Python backend image and the API-host Compose
topology for the NovAIC backend stack.

The image contains:

- Entangled
- Gateway
- Business
- Device
- Queue Service and worker roles
- Service Registry
- Blob Service
- Sandboxd
- Cortex

Build from the repository root:

```bash
docker build -f docker/api-backend/Dockerfile -t novaic/api-backend:local .
```

CI/CD should deploy immutable refs with `./deploy services-image <namespace> <image-ref>`. Local `:local` images and remote builds are fallback-only.

## Compose Topology

`compose.yaml` runs the backend services and worker roles from the shared image:

- Entangled, Gateway, Business, Device, Queue Service, Service Registry,
  Blob Service, Sandboxd, and Cortex.
- Two control task workers, two execution task workers, two saga workers, one
  session outbox worker, one saga outbox worker, one runtime health worker, one
  scheduler, and one subscriber.

The topology intentionally uses `network_mode: host` for the first API-host
cutover. Prod uses `199xx`; staging uses `299xx`. Service names do not change
between environments; isolation comes from `NOVAIC_NAMESPACE`, Compose project,
registry namespace, and namespaced data/secret paths.

Postgres, Host infra Docker, and LLM Factory remain external local dependencies
for this Compose package:

- Postgres: `127.0.0.1:5432`, DSN files under `/opt/novaic/postgres/secrets/<namespace>`.
- Host infra Docker: Redis on namespace DBs (`prod` = DB 0, `staging` = DB 1),
  plus coturn and QUIC via novaic-quic-service. Deploy with `./deploy host-infra`.
- LLM Factory: prod `127.0.0.1:19990`, staging `127.0.0.1:29990`.

Service Registry runs inside this Compose topology on prod `127.0.0.1:19991`
or staging `127.0.0.1:29991`.
It stores runtime service instances in Postgres through
`/opt/novaic/postgres/secrets/<namespace>/novaic_registry_dsn`.

HTTP services start through `common.service_runtime`: each service waits for its
local health endpoint, registers a fresh instance, sends heartbeats, and
deregisters on shutdown. Callers and worker roles receive dependency URLs via
`--namespace <namespace> --require-service service_name=--flag` bindings
resolved from the same namespace Service Registry.
`services.json` remains manifest/bootstrap metadata; it is not a runtime
fallback source.

## Runtime Inputs

The Compose file expects namespace-specific API-host paths:

- `/opt/novaic/data/<namespace>`
- `/opt/novaic/postgres/secrets/<namespace>`
- `/opt/novaic/etc/<namespace>`

Required DSN files include `/opt/novaic/postgres/secrets/<namespace>/novaic_registry_dsn`
for the centralized Service Registry.

`/opt/novaic/etc/<namespace>/secrets.json` is the runtime secret overlay consumed by
`common.strict_config` inside containers and by `write_env.py` during deploy.
The committed `novaic-common/config/services.json` declares secret field names
only; it must not carry real secret values.

Use `env.example` only as a shape reference. Real values belong in an untracked
API-host env file such as `/opt/novaic/docker/api-backend.<namespace>.env`; do
not commit that file.

Validate the topology without starting services:

```bash
docker compose \
  --env-file docker/api-backend/env.example \
  -f docker/api-backend/compose.yaml \
  config
```

Also verify the explicit prod/staging examples:

```bash
docker compose --env-file docker/api-backend/env.prod.example -f docker/api-backend/compose.yaml config
docker compose --env-file docker/api-backend/env.staging.example -f docker/api-backend/compose.yaml config
```

Run on the API host after the deployment env file and image tag are prepared:

```bash
docker compose \
  --env-file /opt/novaic/docker/api-backend.prod.env \
  -f /opt/novaic/docker/api-backend/compose.yaml \
  up -d --no-build
```

The image intentionally does not start a default service because every role
needs explicit ports, URLs, secrets, and data mounts.
