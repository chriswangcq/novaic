# LLM Factory Docker Package

This package mirrors the production Factory container boundary on `api.gradievo.com`.

Remote layout is namespace-aware. The compose package stays at
`/opt/novaic/llm-factory`, while runtime state lives below the namespace
directory.

- Compose directory: `/opt/novaic/llm-factory`
- App build context: `/opt/novaic/llm-factory/app`
- Compose file: `/opt/novaic/llm-factory/docker-compose.yml`
- Compose env: `/opt/novaic/llm-factory/<namespace>/compose.env`
- Runtime env: `/opt/novaic/llm-factory/<namespace>/runtime.env`
- Config/data volume: `/opt/novaic/llm-factory/<namespace>/data`
- Secrets volume: `/opt/novaic/llm-factory/<namespace>/secrets`

`docker/llm-factory/env.prod.example` and
`docker/llm-factory/env.staging.example` are the renderable examples. Prod uses
host port `19990`; staging uses `29990`. Both keep the service name
`llm-factory`; environment isolation comes from `NOVAIC_NAMESPACE`, Compose
project name, runtime paths, and host port.

`./deploy factory` currently syncs the local `novaic-llm-factory` app source and
this Docker package to the API host, verifies the remote runtime inputs exist,
then runs Docker Compose. The image-based deploy path should pass an immutable
`NOVAIC_LLM_FACTORY_IMAGE` and use `docker compose up --no-build` after pulling
that image.

Factory is still an explicit dependency for callers in this package. The long
term platform path is to register `llm_factory` in the namespace-aware service registry and have Agent Runtime discover the same namespace Factory; do not add
a static fallback while making that change.

Do not commit or print `runtime.env`, `data/config.json`, or files under
`secrets/`.
