# Cross-repo generation residue guard matrix

## Problem

After runtime and Cortex patches, the cross-repo guards must be rerun and classified so the parent problem can prove no unclassified live generation residue remains.

## Success Criteria

- Rerun the generation coercion guard over runtime and Cortex target directories.
- Rerun the active/finalize/archive residue guards.
- Provide a concise matrix classifying each remaining hit as fixed, safe helper/test code, or safe boundary signature.
- No live path remains that silently defaults generation or acts on stale active session generation.
- This belongs under P385 because source guard proof is required after patching both repositories.
