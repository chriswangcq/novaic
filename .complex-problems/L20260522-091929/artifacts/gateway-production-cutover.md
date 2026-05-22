# Gateway Production Postgres Cutover

Cutover time: 2026-05-22 12:12 Asia/Shanghai  
Host: `api.gradievo.com`  
Scope: P032 production Gateway auth/config cutover from SQLite to Postgres.

## Backup

Cutover archive:

```text
/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z
```

Backed up:

- `gateway.db`
- `gateway.db.sha256`
- `source-counts.txt`
- `start.sh.before`
- `gateway-code-before.tar`
- `GATEWAY_POSTGRES_CUTOVER.md`

Source counts before migration:

```text
users|1
refresh_tokens|26
config|5
```

## Deployment

Deployed Gateway files:

- `main_gateway.py`
- `gateway/db/access.py`
- `gateway/db/postgres.py`
- `gateway/db/schema.py`
- `gateway/entity/store.py`
- `requirements.txt`
- `scripts/migrate_gateway_sqlite_to_postgres.py`

Remote compile check passed:

```text
python -m py_compile main_gateway.py gateway/db/access.py gateway/db/postgres.py gateway/db/schema.py gateway/entity/store.py scripts/migrate_gateway_sqlite_to_postgres.py
```

## Migration

Migration command used the prepared DSN file and did not print credentials:

```text
scripts/migrate_gateway_sqlite_to_postgres.py --sqlite-db /opt/novaic/data/gateway.db --postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn --replace
```

Migration result:

```text
source_counts=users:1,refresh_tokens:26,config:5
target_counts=users:1,refresh_tokens:26,config:5
```

## Runtime Switch

`/opt/novaic/start.sh` now starts Gateway with:

```text
--db-backend postgres --postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn
```

`systemctl restart novaic` completed and `systemctl is-active novaic` returned:

```text
active
```

Gateway process after restart:

```text
/opt/novaic/services/novaic-gateway/main_gateway.py ... --db-backend postgres --postgres-dsn-file <redacted>
```

Gateway log evidence:

```text
DB backend: postgres
[DB] Connecting to Gateway Postgres
[DB] Postgres schema version updated to 63
Ready (thin Gateway - auth, WS/SSE, files, internal auth endpoints)
```

## Verification

Gateway health:

```json
{"status":"healthy","version":"0.3.0","agent_initialized":true,"mcp_healthy":false,"tools_count":0,"vmcontrol_healthy":false}
```

Auth negative-login smoke:

```text
auth_negative_login_http=401
{"detail":"Invalid email or password"}
```

Postgres counts after restart:

```text
users|1
refresh_tokens|26
config|5
```

No active SQLite holder:

```text
lsof /opt/novaic/data/gateway.db -> no output
```

Active-path cleanup:

```text
find /opt/novaic/data -maxdepth 1 -name "gateway.db*" -> no output
/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/gateway.db.removed-from-data-dir|176128|600|root:root
```

Other services after the shared restart:

- Entangled `/v1/ready`: ready
- Business `/health`: healthy
- Device `/health`: healthy
- Cortex `/ready`: ok
- Queue `/health`: healthy, still on `/opt/novaic/data/queue.db`

## Documentation

Updated:

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`
- `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/GATEWAY_POSTGRES_CUTOVER.md`

## Rollback

Rollback evidence is in the cutover archive. To roll back:

1. Restore `/opt/novaic/start.sh` from `start.sh.before` or remove the Gateway Postgres flags.
2. Restore previous Gateway code from `gateway-code-before.tar` if needed.
3. Restore `gateway.db.removed-from-data-dir` to `/opt/novaic/data/gateway.db`.
4. Restart `novaic`.
5. Verify Gateway `/api/health`.
