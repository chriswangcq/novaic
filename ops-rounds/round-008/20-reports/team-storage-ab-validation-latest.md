# Storage-A/B Restore Validation Evidence — Round 008

- status: DONE
- round: 008
- executed_at_utc: 2026-02-19T03:50:16Z
- command: `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- VALIDATION_OK: true

## Backup Output
```
BACKUP_DIR=/tmp/novaic-storage-ab-validate-<pid>/backups/validation-run
MANIFEST=/tmp/novaic-storage-ab-validate-<pid>/backups/validation-run/manifest.json
```

## Restore Output
```
RESTORE_OK=true
RESTORED_FROM=/tmp/novaic-storage-ab-validate-<pid>/backups/validation-run
TARGET_DIR=/tmp/novaic-storage-ab-validate-<pid>/data
```

## Validation Summary
- file restore check: PASS (`files/images/agent-demo/sample.txt` restored)
- db restore check: PASS (`tool_results` contains `trs_demo_001`)
