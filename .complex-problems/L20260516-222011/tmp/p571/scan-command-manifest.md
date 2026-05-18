# P571 Scan Command Manifest

## Scope

This manifest makes P571 reproducible from durable file evidence. It records the commands that generated the `BlobObjectStore` adapter boundary artifacts, the artifact paths, and the criteria each artifact supports.

## Command 1: BlobObjectStore / Adapter Scan

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p571/blobobjectstore-scan.txt`

Exact command:

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p571
{
  printf '%s\n' '## BlobObjectStore / object-store adapter terms'
  rg -n 'BlobObjectStore|ObjectStore|object adapter|object_store|object store|FileAuthority|Blob.*Store|list_object_keys|\.key\(' \
    novaic-cortex/novaic_cortex \
    novaic-cortex/tests \
    novaic-logicalfs/logicalfs \
    novaic-logicalfs/tests

  printf '\n%s\n' '## direct blob / namespace references near Cortex and LogicalFS adapters'
  rg -n 'blob://|blob_service|BlobService|cortex-payload|runtime-artifact|namespace|tenant|object_key|blob_ref' \
    novaic-cortex/novaic_cortex \
    novaic-cortex/tests \
    novaic-logicalfs/logicalfs \
    novaic-logicalfs/tests
} > .complex-problems/L20260516-222011/tmp/p571/blobobjectstore-scan.txt
```

Criteria supported:

- Finds `BlobObjectStore`, `LogicalObjectStore`, `StoreBackedLogicalFileAuthority`, Cortex registry wiring, direct namespace use, and payload/artifact blob references.

## Command 2: Boundary Slices

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p571/blobobjectstore-slices.txt`

Exact command:

```bash
{
  printf '%s\n' '## Cortex registry uses BlobObjectStore only as LogicalFS object adapter'
  nl -ba novaic-cortex/novaic_cortex/registry.py | sed -n '1,90p'

  printf '\n%s\n' '## Cortex workspace authority builds LogicalFS authority from object store'
  nl -ba novaic-cortex/novaic_cortex/workspace_authority.py | sed -n '1,80p'

  printf '\n%s\n' '## LogicalFS object authority contract and key mapping'
  nl -ba novaic-logicalfs/logicalfs/authority.py | sed -n '1,215p'

  printf '\n%s\n' '## BlobObjectStore implementation'
  nl -ba novaic-logicalfs/logicalfs/blob_store.py | sed -n '1,150p'

  printf '\n%s\n' '## Cortex payload blob adapter is payload-specific, not workspace authority'
  nl -ba novaic-cortex/novaic_cortex/blob_payload.py | sed -n '1,170p'
} > .complex-problems/L20260516-222011/tmp/p571/blobobjectstore-slices.txt
```

Criteria supported:

- Reads line-numbered slices for Cortex registry wiring, Workspace authority construction, LogicalFS object authority, BlobObjectStore implementation, and payload-specific blob adapter.

## Classification Conclusion

`BlobObjectStore` is intended infrastructure: it is a generic LogicalFS object-store adapter under `StoreBackedLogicalFileAuthority`, not a public Cortex workspace semantic API. Cortex creates it in `WorkspaceRegistry`, then immediately wraps it with `build_workspace_file_authority()` before constructing `Workspace`.

No high-confidence P554 remediation candidate is forwarded from P571. Payload blob references in `blob_payload.py` are separate payload externalization, not realtime RO/RW workspace authority.
