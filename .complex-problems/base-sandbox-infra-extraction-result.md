# Base sandbox infrastructure extraction result

## Summary

Stable business-agnostic sandbox primitives were extracted into `novaic-common/common/sandbox`, and Cortex was migrated to consume them. Cortex now keeps only product semantics: Workspace/LogicalFS, `/cortex` stable paths, `/ro`/`/rw`, shell capabilities, and policy/orchestration.

## Done

- Audited extraction boundary and protected Cortex-specific concepts from over-extraction.
- Added common base modules:
  - `common.sandbox.process`
  - `common.sandbox.mount_namespace`
  - `common.sandbox.filesystem`
- Added common tests in `novaic-common/tests/test_sandbox_infra.py`.
- Migrated Cortex:
  - `sandbox.py` uses `common.sandbox.process.AsyncProcessRunner`.
  - `logical_fs.py` uses common mount namespace and filesystem helpers.
  - Deleted `novaic_cortex/sandbox_exec.py`.
- Verified both repos and residue.

## Evidence

- `novaic-common`: `145 passed`.
- `novaic-cortex`: `342 passed, 41 skipped`.
- Residue scan found no `novaic_cortex.sandbox_exec`, no `class SandboxExec`, no old local generic filesystem helpers, and no old command rewrite/lazy RO helpers.

## Final Boundary

Common/base:

```text
common.sandbox.process
common.sandbox.mount_namespace
common.sandbox.filesystem
```

Cortex/product:

```text
novaic_cortex.logical_fs
novaic_cortex.sandbox
novaic_cortex.shell_capabilities
novaic_cortex.workspace
```

## Residual Risk

Production mount smoke was not run in this pass. The skipped Cortex shell tests are expected on hosts without root/unshare/mount.
