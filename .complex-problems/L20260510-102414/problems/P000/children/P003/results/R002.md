# Workspace dependency boundary result

## Summary

LogicalFS no longer reaches into Workspace private store/key internals. Workspace now exposes a public recursive logical tree-byte port, and LogicalFS consumes that port.

## Done

- Added `Workspace.read_tree_bytes(path, *, concurrency=16)`.
- The new Workspace method returns `(relative_posix_path, bytes)` for files under a logical `/ro/` or `/rw/` prefix.
- Updated `MountNamespaceLogicalFS._estimate_sync_bytes` and `_materialize_logical_view` to use `Workspace.read_tree_bytes`.
- Removed `_key` import and direct `workspace._store` usage from `logical_fs.py`.

## Evidence

- `novaic_cortex/workspace.py` now imports `asyncio` and owns recursive store listing/byte reads behind `read_tree_bytes`.
- `novaic_cortex/logical_fs.py` imports only `Workspace`, not `_key`.
- `rg` found no `_store`, `_key`, or `list_recursive` usage in `logical_fs.py`.
- Compile/import smoke passed with `PYTHONPATH=../novaic-common:.`.
- Targeted pytest command passed locally with `6 passed, 32 skipped`.

## Notes

The new method intentionally preserves concurrent byte reads so the boundary cleanup does not make RO/RW materialization more serial.
