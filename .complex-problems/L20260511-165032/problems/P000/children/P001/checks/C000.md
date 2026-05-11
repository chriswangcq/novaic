# LogicalFS and Sandbox adapter audit check

## Summary

Audit succeeded for this boundary: the full `/ro` shell miss is no longer present, no local sandbox fallback is live, and the remaining analogous risk is clearly identified as full `/rw/` materialization.

## Evidence

- `R000` inspected `sandbox.py`, `logical_fs.py`, `workspace.py`, and relevant tests.
- `sandbox.py` fails explicitly without sandboxd rather than falling back to local execution.
- `logical_fs.py` scopes RO materialization to current root/wake metadata and event files.
- `logical_fs.py` still recursively materializes `/rw/` through `_add_tree(files, "/rw/")`.

## Criteria Map

- Broad `/ro` shell materialization absent from live path: satisfied.
- Local fallback identified: satisfied; no live fallback found.
- Recursive reads remaining in shell path: satisfied; `/rw/` full tree identified.
- Evidence pointers recorded: satisfied.

## Execution Map

- `T001` executed source searches and code inspection.
- `R000` recorded confirmed clean paths and the remaining RW gap.

## Stress Test

If an agent accumulates many RW artifacts, shell startup can still grow with RW size because the current implementation copies the whole `/rw/` tree into each sandbox view. This reproduces the shape of the original RO issue on a smaller but real surface.

## Residual Risk

Medium. The risk is not currently causing the observed production stall after the RO fix, but it is a similar unintegrated adapter shape and should be fixed in the next implementation pass.
