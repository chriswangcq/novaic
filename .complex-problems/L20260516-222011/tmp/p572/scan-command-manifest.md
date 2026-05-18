# P572 Scan Command Manifest

## Scope

This manifest makes P572 reproducible from durable file evidence. It records the commands that generated LogicalFS authority/key-prefix artifacts, output paths, and criteria mapping.

## Command 1: LogicalFS Authority Scan

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p572/logicalfs-authority-scan.txt`

Exact command:

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p572
{
  printf '%s\n' '## LogicalFS authority/key-prefix/materialize/diff/writeback terms'
  rg -n 'LogicalFileAuthority|LogicalObjectStore|StoreBackedLogicalFileAuthority|logical_to_object_key|owner_prefix|ro_prefix|rw_prefix|normalize|materialize|diff|patch|writeback|release|snapshot|list_recursive|move_prefix|object key|object-store' \
    novaic-logicalfs/logicalfs \
    novaic-logicalfs/tests \
    novaic-cortex/novaic_cortex/workspace_authority.py \
    novaic-cortex/tests/test_paths_adversarial.py \
    novaic-cortex/tests/test_workspace_authority.py

  printf '\n%s\n' '## direct logicalfs export/public API terms'
  rg -n 'BlobObjectStore|StoreBackedLogicalFileAuthority|LogicalFileAuthorityLayout|logical_to_object_key|LocalLogicalFSProvider|LogicalFSView|LogicalFSSnapshot|LogicalFSPatch' \
    novaic-logicalfs/logicalfs \
    novaic-logicalfs/tests \
    novaic-cortex/novaic_cortex/logical_fs.py \
    novaic-cortex/tests/test_paths_adversarial.py \
    novaic-cortex/tests/test_workspace_authority.py
} > .complex-problems/L20260516-222011/tmp/p572/logicalfs-authority-scan.txt
```

Criteria supported:

- Finds LogicalFS authority, key-prefix, object-store protocol, snapshot/materialize/patch, stable path, and export terms.

## Command 2: LogicalFS Authority Slices

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p572/logicalfs-authority-slices.txt`

Exact command:

```bash
{
  printf '%s\n' '## LogicalFS contracts'
  nl -ba novaic-logicalfs/logicalfs/contracts.py | sed -n '1,100p'

  printf '\n%s\n' '## LogicalFS authority path/key semantics'
  nl -ba novaic-logicalfs/logicalfs/authority.py | sed -n '1,215p'

  printf '\n%s\n' '## Local materialization and patch observation'
  nl -ba novaic-logicalfs/logicalfs/local.py | sed -n '1,190p'

  printf '\n%s\n' '## LogicalFS public exports'
  nl -ba novaic-logicalfs/logicalfs/__init__.py | sed -n '1,60p'

  printf '\n%s\n' '## Authority and adversarial tests'
  nl -ba novaic-logicalfs/tests/test_authority.py | sed -n '1,140p'
  nl -ba novaic-logicalfs/tests/test_logicalfs.py | sed -n '1,120p'
  nl -ba novaic-cortex/tests/test_paths_adversarial.py | sed -n '1,155p'
  nl -ba novaic-cortex/tests/test_workspace_authority.py | sed -n '1,60p'
} > .complex-problems/L20260516-222011/tmp/p572/logicalfs-authority-slices.txt
```

Criteria supported:

- Reads contracts, authority mapping, local materialization/patch observation, public exports, and tests with line numbers.

## Classification Conclusion

LogicalFS currently owns realtime logical `/ro` and `/rw` semantics through explicit contracts, path normalization, owner-prefix key mapping, local snapshot materialization, and RW patch observation. The generic object-store protocol is below LogicalFS; object keys are implementation detail. No high-confidence P554 remediation candidate is forwarded from P572.
