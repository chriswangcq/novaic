# Compare RO/RW Optimization Models

## Problem

Compare realistic optimization models for `/cortex/ro` and `/cortex/rw` mounting in this system. Include lazy RO, manifest/delta sync, persistent cache, FUSE/virtual filesystem, CLI-native object access, and hybrids.

## Success Criteria

- Compare each candidate on performance, correctness, operational complexity, and fit with the current architecture.
- Explicitly call out which options are poor fits or too heavy.
- Preserve the stable shell contract as a first-class constraint.
