# LogicalFS Object Authority And Key Prefix Classification

## Problem

Classify LogicalFS authority code and key-prefix semantics to confirm LogicalFS owns realtime file semantics while object storage remains an implementation detail below it.

## Success Criteria

- Records exact scan commands and outputs for LogicalFS object-store, namespace, key-prefix, snapshot, materialize, diff, and writeback terms.
- Reads relevant LogicalFS code slices with line references.
- Separates intended object-store-backed file authority from risky blob-as-filesystem semantics.
- Identifies any remediation candidate for P554.
