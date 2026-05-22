# Device DB Cleanup Verification

Snapshot time: 2026-05-22 11:56 CST  
Host: `api.gradievo.com`  
Scope: P011 verification of already-applied `device.db` cleanup. No new production cleanup, data mutation, restart, or cutover was performed during this verification pass.

## Active File State

`/opt/novaic/data/device.db` is absent. A direct remote check returned success for `test ! -e /opt/novaic/data/device.db`, and `find /opt/novaic/data -maxdepth 1 -name 'device.db*'` returned no files.

Archive evidence:

```text
archive=/opt/novaic/residue-archive/device-db-delete-20260522T020133Z/device.db size=20480 mode=640 owner=root:root
```

## Runtime State

Device process:

```text
3473537 /opt/novaic/services/novaic-gateway/.venv/bin/python /opt/novaic/services/novaic-device/main_device.py --host 127.0.0.1 --port 19993 --data-dir /opt/novaic/data --gateway-url http://127.0.0.1:19999 --business-url http://127.0.0.1:19998
```

Device health:

```json
{"status":"healthy","service":"device","version":"0.2.0"}
```

## Code Reference Check

Remote search under `/opt/novaic/services/novaic-device` and `/opt/novaic/start.sh` for these patterns returned no matches:

- `device.db`
- `db_access`
- `init_database`
- `close_database`

Remote `find /opt/novaic/services/novaic-device -name db_access.py -print` returned no files.

`device/ssh_keys.py` now uses a file-backed SSH key store under `$NOVAIC_DATA_DIR/.ssh`:

```text
root-readable files under ``$NOVAIC_DATA_DIR/.ssh`` so the service does not
self.ssh_dir = Path(ServiceConfig.DATA_DIR) / ".ssh"
keys_{user}.json
id_ed25519_{user}_{key_id}
id_ed25519_{user}_{key_id}.pub
```

## Central Classification Note

`/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` records `/opt/novaic/data/device.db` as deleted/archived residue:

```text
Removed from active path and archived at /opt/novaic/residue-archive/device-db-delete-20260522T020133Z/device.db. Restart and SSH-key route verification confirmed it is not recreated.
```

## Rollback / Restoration Notes

Rollback to the previous SQLite-backed Device path would require both:

1. Restore the archived file from `/opt/novaic/residue-archive/device-db-delete-20260522T020133Z/device.db` to `/opt/novaic/data/device.db`.
2. Re-deploy the previous Device code path that initialized `device.db` and imported `device/db_access.py`.

The current intended direction is no SQLite fallback for Device, so the archive should be retained only as rollback evidence until the agreed retention window expires.

## Conclusion

`device.db` has been removed from the active path, documented as deleted/archived residue, and no current Device startup or code path found in this verification pass can recreate it.
