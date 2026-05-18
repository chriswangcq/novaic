# P388 cross-repo generation residue guard matrix check

## Summary

Not successful. The guard matrix did the right skeptical thing and found additional generation/defaulting residue beyond the original narrow target. Because R372 has known gaps and no final clean classification, P388 cannot close as success.

## Blocking Gaps

- The pure session FSM reducer still silently coerces `finalize_generation` and current state generation with raw `int(... or 0)`.
- Session repo state reconstruction helpers still silently default generation to `0` from active/session state dictionaries.
- Session ledger/audit and broader FSM infrastructure have remaining raw generation/default adapters that are not yet classified as safe or fixed.
- The result explicitly says the matrix is not clean enough to close the parent.

## Result IDs

- R372
