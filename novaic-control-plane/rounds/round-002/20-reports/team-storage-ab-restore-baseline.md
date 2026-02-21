# Storage-A/B Restore Baseline (Round 002)

- command: `bash novaic-backend/scripts/storage_ab_backup.sh --data-dir <tmp> --backup-root <tmp> --label round002-baseline`
- command: `bash novaic-backend/scripts/storage_ab_restore.sh --backup-dir <resolved> --target-dir <tmp> --yes`
- expected_marker: `RESTORE_OK=true`
- backup_dir: `/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-round002-storage-restore-35988/backups/round002-baseline`

## Backup Output
```
BACKUP_DIR=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-round002-storage-restore-35988/backups/round002-baseline
MANIFEST=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-round002-storage-restore-35988/backups/round002-baseline/manifest.json
```

## Restore Output
```
RESTORE_OK=true
RESTORED_FROM=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-round002-storage-restore-35988/backups/round002-baseline
TARGET_DIR=/var/folders/n3/_7qrtb716jg07p9d71216l3m0000gn/T//novaic-round002-storage-restore-35988/restore-target
```

## Post-check
- RESTORE_FILE_CHECK=PASS
- RESTORE_DB_CHECK=PASS
