# P021 LogicalFS Authority Check

## Summary

Success for P021. The generic LogicalFS live authority exists in `novaic-logicalfs`, is exported from the package API, uses explicit layout inputs, depends only on a generic object-store Protocol, and is covered by focused tests.

## Evidence

- `novaic-logicalfs/logicalfs/authority.py` defines `LogicalObjectStore`, `LogicalFileAuthorityLayout`, `StoreBackedLogicalFileAuthority`, and `logical_to_object_key`.
- `novaic-logicalfs/logicalfs/contracts.py` defines LogicalFS-owned `LogicalFSDirectoryEntry` and `LogicalObjectInfo`.
- `novaic-logicalfs/logicalfs/__init__.py` exports the new authority and contract types.
- `novaic-logicalfs/tests/test_authority.py` covers path mapping, file operations, listing, tree reads, moving, layout initialization, and invalid path rejection.
- Test command passed: `9 passed in 0.03s`.
- Dependency scan found no `novaic_cortex` import inside `novaic-logicalfs`.

## Criteria Map

- Public API exposure: satisfied by `logicalfs/__init__.py` exports.
- Explicit layout mapping: satisfied by `LogicalFileAuthorityLayout(owner_prefix, ro_prefix, rw_prefix)` and `logical_to_object_key`.
- Generic object store: satisfied by `LogicalObjectStore` Protocol and test `MemoryObjectStore` with no Cortex import.
- Unit coverage: satisfied by `tests/test_authority.py`.
- Not merely Cortex copy: satisfied because the API uses generic owner/layout/object-store names and returns LogicalFS types instead of Cortex `FileEntry` / `CortexStore`.

## Execution Map

- Added authority code and contract exports.
- Added tests for the new authority behavior.
- Ran LogicalFS package tests and dependency scan.

## Stress Test

- Checked invalid paths (`/etc/passwd`, `..`, NUL) to make sure authority rejects non-logical or unsafe paths.
- Checked both `/ro` and `/rw` mappings through non-default prefixes.
- Checked recursive read/move/list behavior because those are the operations Cortex cutover will depend on.

## Residual Risk

- Cortex has not yet been switched to this authority; P023 covers active cutover.
- Blob object persistence has not yet been moved below this boundary; P022 covers adapter ownership.
- Old Cortex authority code still exists until P024 cleanup.

## Result IDs

- R020
