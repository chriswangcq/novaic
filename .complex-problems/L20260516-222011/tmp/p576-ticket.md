# Audit Shell History Tool Output Contract

## Problem Definition

P576 must verify the shell/tool output contract: bounded terminal text is what enters LLM history and monitor previews, full details remain recoverable via Cortex RO step/payload files, and artifacts are referenced through manifests/BlobRefs rather than inline media bytes.

## Proposed Solution

Split the audit into shell execution/wrapper output, Cortex step/payload persistence, and tests/guardrails. Each child should record exact scans, cite code/test slices, and classify any risky large/raw-media output residue.

## Acceptance Criteria

- Shell output wrapper/truncation behavior is audited with evidence.
- Cortex RO step/payload persistence and payload refs are audited with evidence.
- Tests/guardrails for shell output contract are mapped and run.
- Risky shell history/media/base64 residue is fixed or forwarded as follow-up.

## Verification Plan

Each split child records evidence and focused tests; parent aggregates only after children are checked successful.

## Risks

- Shell output contract spans runtime, Cortex, monitor, and CLI wrappers; one-go would likely miss old paths.
- Full output persistence can be legitimate if stored as payload files rather than history text.

## Assumptions

- The desired contract is terminal-like bounded text in LLM history plus RO/payload recovery for full details.
