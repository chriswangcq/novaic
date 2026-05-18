# Cortex BlobObjectStore Adapter Boundary Classification

## Problem

Classify `BlobObjectStore` and Cortex registry/store adapter usage to determine whether it is strictly a LogicalFS object-store adapter below Workspace semantics or whether it gives Cortex a direct blob-as-workspace authority bypass.

## Success Criteria

- Records exact scan commands and outputs for `BlobObjectStore`, `ObjectStore`, object adapter, registry, and Cortex store terms.
- Reads relevant Cortex/LogicalFS adapter slices with line references.
- Classifies each hit bucket as intended, risky, removable, or follow-up.
- Identifies any remediation candidate for P554.
