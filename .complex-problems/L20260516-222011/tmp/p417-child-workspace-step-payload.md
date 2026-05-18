# Workspace step and payload normalization cleanup

## Problem

Workspace step writing and payload normalization are the bridge between shell/tool outputs and ContextEvents. They must enforce pointer-oriented payloads and avoid inline result compatibility.

## Success Criteria

- Inspect `workspace.py` step writing, payload writing, payload reading, and manifest code.
- Verify tool steps reject inline `result` and externalize or reference payloads explicitly.
- Remove stale compatibility branches if they allow large inline payloads or ambiguous payload refs.
- Add focused tests if behavior changes.
- Run workspace/payload/step projection tests.

