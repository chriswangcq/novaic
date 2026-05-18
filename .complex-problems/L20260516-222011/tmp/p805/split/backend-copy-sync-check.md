# Backend Startup Resource And Generated Copy Synchronization

## Problem

The app has source resources and generated asset copies for backend startup scripts/config. After the remediation children edit source-of-truth files, committed duplicates must be synchronized so the app does not ship different behavior than the source tree.

## Success Criteria

- Resource and generated packaged startup scripts/config are byte-identical where they are intended duplicates.
- Generated/resource backend directories are compared and any intentional binary differences are documented in the result.
- `bash -n` passes for all committed startup scripts.
- Final targeted scans across app scripts/resources/generated assets show no stale startup graph residues from the remediated issues.
