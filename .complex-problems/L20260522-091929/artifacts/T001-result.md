# T001 Result: Local Postgres Docker Foundation

## Summary

Provisioned a local-only Postgres Docker foundation on `api.gradievo.com` under `/opt/novaic/postgres`.

## Done

Created:
- `/opt/novaic/postgres/docker-compose.yml`
- `/opt/novaic/postgres/secrets/*_password` with `0600 root:root`
- `/opt/novaic/postgres/initdb/01-create-novaic-databases.sh`
- `/opt/novaic/postgres/bin/backup-all.sh`
- `/opt/novaic/postgres/bin/restore-all.sh`
- `/opt/novaic/postgres/README.md`
- `/opt/novaic/postgres/data`
- `/opt/novaic/postgres/backups`

The running container is `novaic-postgres` from `postgres:16-alpine`, with restart policy `unless-stopped`, data persisted under `/opt/novaic/postgres/data`, and port mapping restricted to `127.0.0.1:5432:5432`.

Fixed a startup/init issue during execution:

The first Postgres boot partially initialized `PGDATA` before the init script could run because the bind-mounted data/init directories had restrictive ownership/permissions for the container user. I fixed this by stopping the stack, clearing the partial data directory, setting the data directory to the Postgres image UID/GID, setting the init directory executable, and restarting.

After restart, the container was healthy but the first verification showed only `novaic_admin`; the per-service init script had been skipped because `PGDATA` was already initialized. I executed the idempotent init script manually inside the container, which created all intended service roles/databases.

## Verification

Container/listener:

```text
novaic-postgres Up 2 minutes (healthy) 127.0.0.1:5432->5432/tcp
LISTEN 0 4096 127.0.0.1:5432 0.0.0.0:* users:(("docker-proxy",pid=3461814,fd=7))
```

Created roles:

```text
novaic_admin
novaic_cortex
novaic_entangled
novaic_gateway
novaic_llm_factory
novaic_queue
```

Created databases:

```text
novaic_cortex
novaic_entangled
novaic_gateway
novaic_llm_factory
novaic_queue
```

Per-service login checks:

```text
novaic_llm_factory@novaic_llm_factory
novaic_entangled@novaic_entangled
novaic_queue@novaic_queue
novaic_gateway@novaic_gateway
novaic_cortex@novaic_cortex
```

Credential/storage permissions:

```text
drwxr-x--- root:root /opt/novaic/postgres
drwx------ 70:70 /opt/novaic/postgres/data
drwxr-x--- root:root /opt/novaic/postgres/secrets
-rw------- root:root /opt/novaic/postgres/secrets/postgres_admin_password
-rw------- root:root /opt/novaic/postgres/secrets/novaic_llm_factory_password
-rw------- root:root /opt/novaic/postgres/secrets/novaic_entangled_password
-rw------- root:root /opt/novaic/postgres/secrets/novaic_queue_password
-rw------- root:root /opt/novaic/postgres/secrets/novaic_gateway_password
-rw------- root:root /opt/novaic/postgres/secrets/novaic_cortex_password
```

Backup proof:

```text
-rw------- 1 root root 2.1K May 22 09:27 /opt/novaic/postgres/backups/novaic-postgres-20260522T012734Z.sql.gz
```

Existing service health after provisioning:

```text
systemctl is-active docker novaic nginx
active
active
active

novaic-llm-factory: running healthy
http://127.0.0.1:19990/health -> {"status":"ok","service":"llm-factory"}
https://api.gradievo.com/health -> {"status":"healthy","version":"0.3.0","agent_initialized":true,"mcp_healthy":false,"tools_count":0,"vmcontrol_healthy":false}
```

## Known Gaps

No application has been cut over to Postgres yet, by design. The Postgres service is ready as infrastructure, but application migrations still need separate tickets with backups, row-count checks, rollback paths, and health checks.

The init script is safe for future empty-volume initialization and was also executed manually once to repair the partial-initialization path.

## Artifacts

- Remote compose stack: `/opt/novaic/postgres/docker-compose.yml`
- Remote init script: `/opt/novaic/postgres/initdb/01-create-novaic-databases.sh`
- Remote backup helper: `/opt/novaic/postgres/bin/backup-all.sh`
- Remote restore helper: `/opt/novaic/postgres/bin/restore-all.sh`
- Backup artifact: `/opt/novaic/postgres/backups/novaic-postgres-20260522T012734Z.sql.gz`
