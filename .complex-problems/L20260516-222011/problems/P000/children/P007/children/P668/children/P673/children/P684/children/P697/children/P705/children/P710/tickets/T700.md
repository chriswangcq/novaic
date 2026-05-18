# Ticket: Cortex boundary discovery and map

## Problem Definition
Discover Cortex entrypoints, launch surfaces, semantic state/context modules, and service dependencies. Produce an evidence-backed boundary map without making implementation changes.

## Proposed Solution
Run targeted scans over `novaic-cortex`, runtime/app launch scripts, docs, and imports. Record entrypoints, state/context modules, dependency boundaries, generated/history separation, and potential residue candidates.

## Acceptance Criteria
- Cortex entrypoint and launch evidence is listed.
- Semantic context/scope/state ownership is mapped.
- LogicalFS/Blob/Sandboxd/Queue/Runtime usage is classified as dependency or orchestration, not ownership.
- Active/generated/historical references are separated.
- Potential active cleanup candidates are listed for P711.

## Verification Plan
Use `find`, `rg`, `sed`, and `python -m py_compile` where useful. Produce artifacts for boundary map, scan commands, scan output, and cleanup candidate disposition.
