# Device/artifact/display boundary remediation

## Problem

Patch safe active stale claims or small contract violations found by the Device/devicectl and artifact/display discovery children. This belongs under P708 because active code/docs must reflect the final media boundary: Device captures, Blob stores bytes, shell returns text/manifests, display projects media to model input.

## Success Criteria

- Discovery cleanup candidates are reviewed and dispositioned.
- Safe active stale docs/code claims are patched.
- Any active large-media-as-text path found in shell/history/context surfaces is patched or split into a blocking subproblem.
- Risky broad changes are not hidden; they become follow-up/spawned problems.
