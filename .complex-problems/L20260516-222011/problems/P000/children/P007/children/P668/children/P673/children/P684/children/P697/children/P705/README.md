# Cortex semantic state/context boundary classification

## Problem
Classify Cortex as a semantic state/context service. Verify entrypoints, launch surfaces, storage/state dependencies, and boundaries relative to LogicalFS, Blob, Sandboxd, Queue, and Runtime.

## Success Criteria
- Cortex entrypoints and launch paths are listed with evidence.
- Cortex role is stated as semantic/context/scope service, not long-term owner of realtime file storage, Blob bytes, or sandbox process execution.
- Dependencies on LogicalFS/Blob/Sandboxd/Queue/Runtime are classified as consumed/integrated services, not ownership.
- Stale misleading Cortex ownership claims are patched or recorded.
