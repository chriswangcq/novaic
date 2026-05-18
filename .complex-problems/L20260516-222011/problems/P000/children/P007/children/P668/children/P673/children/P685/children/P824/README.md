# Architecture docs topology alignment

## Problem

Architecture docs (service-topology.md, runtime-architecture.md, cortex docs, etc.) that reference service ports or topology may contain stale descriptions. Compare against P684 classification evidence and patch low-risk stale wording.

## Success Criteria

- All docs referencing service ports (19993-19999, 19900) are located and compared.
- Stale service descriptions are updated to match current topology.
- Doc lint passes for changed files.
