# Storage-A/B Restore Validation Evidence

- status: DONE
- executed_at_utc: 2026-02-19T02:40:47Z
- command: `bash novaic-backend/scripts/storage_ab_validate_restore.sh`
- temp_data_dir: `/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/data`
- backup_dir: `/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/backups/validation-run`

## Backup Output
```
BACKUP_DIR=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/backups/validation-run
MANIFEST=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/backups/validation-run/manifest.json
```

## Restore Output
```
RESTORE_OK=true
RESTORED_FROM=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/backups/validation-run
TARGET_DIR=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-storage-ab-validate-6718/data
```

## Validation Summary
- file restore check: PASS (`files/images/agent-demo/sample.txt` restored)
- db restore check: PASS (`tool_results` contains `trs_demo_001`)
