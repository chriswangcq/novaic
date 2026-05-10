# Add explicit Workspace tree-byte port for LogicalFS

## Problem Definition

After module extraction, LogicalFS still depends on `Workspace._store` and `_key`, which are private implementation details. That obscures the intended layering.

## Proposed Solution

Add a small public Workspace method that returns recursive `(relative_path, bytes)` entries for a logical `/ro/` or `/rw/` subtree. Update LogicalFS to consume this Workspace port instead of store keys.

## Acceptance Criteria

- `logical_fs.py` no longer imports `_key`.
- `logical_fs.py` no longer references `workspace._store`.
- Workspace exposes a public method with logical-path semantics, not blob/store-key semantics.
- Existing LogicalFS behavior is preserved.

## Verification Plan

- Compile/import checks.
- Run targeted workspace/logicalfs/sandbox tests.
- Residue scan for `_store` usage inside `logical_fs.py`.

## Risks

- A naive sequential implementation could worsen RO materialization latency.

## Assumptions

- The method can use Workspace internals because Workspace is the owner of logical path-to-store mapping.
