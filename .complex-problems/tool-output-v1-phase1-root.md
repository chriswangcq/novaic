# ToolOutputV1 Phase 1 substrate implementation

## Problem

Implement the Phase 1 substrate from the shell-boundary construction plan: a pure, deterministic `ToolOutputV1` / artifact manifest contract in Runtime. This should not yet change tool execution behavior; it should provide the stable output envelope that later phases will wire into Runtime executors, Cortex projection, display, device tools, and shell capabilities.

## Success Criteria

- Add a small Runtime module defining `ToolOutputV1`, `ArtifactManifest`, event manifest, diagnostics, and helper constructors.
- Constructors are pure: no hidden time, UUID, env, filesystem, DB, or network reads.
- Text output is bounded deterministically and records truncation.
- Artifact manifests carry URI, modality, optional mime/size/hash/source/access/projection/retention metadata.
- Invalid artifacts fail fast for empty URI, invalid modality, or negative size.
- Unit tests cover serialization, truncation, artifact validation, error output, and explicit dependency boundaries.
- No existing Runtime tool behavior is changed in this phase.
