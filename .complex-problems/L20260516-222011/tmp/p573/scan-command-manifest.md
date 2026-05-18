# P573 Scan Command Manifest

## Primary Scan

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p573
{
  printf '%s\n' '## Blob Service namespace/object/upload/download terms'
  rg -n 'namespace|blob_ref|blob_id|upload|download|objects|_list|_move-prefix|runtime-artifact|cortex-payload|X-Tenant-ID|tenant_id|source_ref|expected_sha256|complete|parts' \
    novaic-blob-service \
    novaic-cortex/novaic_cortex/blob_payload.py \
    novaic-cortex/novaic_cortex/shell_capabilities.py \
    novaic-cortex/tests/test_shell_capabilities_blob_contract.py \
    novaic-logicalfs/logicalfs/blob_store.py \
    novaic-logicalfs/tests/test_blob_store.py

  printf '\n%s\n' '## filesystem/workspace semantic terms near Blob Service'
  rg -n '/ro|/rw|workspace|LogicalFS|file authority|filesystem|directory|prefix|artifact|payload|object store|cheap byte' \
    novaic-blob-service \
    novaic-cortex/novaic_cortex/blob_payload.py \
    novaic-cortex/novaic_cortex/shell_capabilities.py \
    novaic-logicalfs/logicalfs/blob_store.py
} > .complex-problems/L20260516-222011/tmp/p573/blob-service-boundary-scan.txt
```

## Focused Evidence Slices

```bash
{
  printf '%s\n' '## Blob Service README boundary'
  nl -ba novaic-blob-service/README.md | sed -n '1,80p'

  printf '\n%s\n' '## Blob ref contract'
  nl -ba novaic-common/common/contracts/blob.py | sed -n '1,180p'

  printf '\n%s\n' '## Byte blob storage service'
  nl -ba novaic-blob-service/blob_service/blob_storage.py | sed -n '1,190p'

  printf '\n%s\n' '## Object storage API service'
  nl -ba novaic-blob-service/blob_service/object_storage.py | sed -n '1,190p'

  printf '\n%s\n' '## HTTP API routes'
  nl -ba novaic-blob-service/blob_service/main.py | sed -n '1,260p'

  printf '\n%s\n' '## Cortex runtime artifact and payload clients'
  nl -ba novaic-cortex/novaic_cortex/shell_capabilities.py | sed -n '259,320p;360,455p'
  nl -ba novaic-cortex/novaic_cortex/blob_payload.py | sed -n '70,130p'

  printf '\n%s\n' '## Blob contract tests'
  nl -ba novaic-cortex/tests/test_shell_capabilities_blob_contract.py | sed -n '90,210p'
  nl -ba novaic-logicalfs/tests/test_blob_store.py | sed -n '1,70p'
} > .complex-problems/L20260516-222011/tmp/p573/blob-service-boundary-slices.txt
```

## Evidence Correction

The first focused-slice attempt referenced the removed path `novaic-blob-service/blob_service/blob_ref.py`.
The corrected evidence reads the shared public BlobRef contract at
`novaic-common/common/contracts/blob.py`, which is the current boundary source.

