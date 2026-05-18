# Shell History Tool Output Contract Inventory

## Problem

Audit shell/tool output projection paths to verify shell returns bounded terminal text and durable artifact manifests, while full details remain recoverable through Cortex RO step/payload files. This belongs under P564 because shell is now the main interface class for many tools and must not leak large media/base64 into LLM history.

## Success Criteria

- Records exact scan commands and outputs for shell tool wrappers, truncation/projection code, monitor display summaries, and Cortex step/payload recording.
- Reads relevant code/test slices with line references.
- Classifies output truncation, artifact manifests, payload refs, and full-output storage paths as intended, risky, removable, or follow-up.
- Verifies the current contract: bounded terminal text in LLM history, full output discoverable via RO/payload files, artifacts referenced by BlobRef.
- Captures any high-confidence risky residue for P554 remediation.
