# Extract stable sandbox infrastructure into base modules

## Problem

The user wants business-agnostic, long-lived modules with stable inputs and outputs to become base infrastructure instead of staying inside Cortex business code. After the LogicalFS layering cleanup, the obvious candidates are generic process execution, mount namespace command construction/capability detection, and filesystem snapshot/diff helpers.

We must avoid over-extracting Cortex semantics. `/ro`, `/rw`, Workspace, Blob, agent identity, and shell capability commands remain Cortex/product concepts. Stable OS/process/filesystem primitives should move to common infrastructure.

## Success Criteria

- Identify which sandbox/logicalfs pieces are business-agnostic versus Cortex-specific.
- Create base modules under `novaic-common` for stable generic pieces.
- Migrate Cortex to consume those base modules.
- Keep one active implementation path; remove or avoid duplicate local copies.
- Add tests at the base module boundary and run common + Cortex verification.
- Do not reintroduce local fallback or old command rewrite behavior.
