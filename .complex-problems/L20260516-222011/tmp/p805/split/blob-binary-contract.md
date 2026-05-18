# Packaged Blob Binary Contract Remediation

## Problem

The packaged backend startup scripts look for `novaic-blob-service`, but the generated packaged backend assets contain `novaic-storage-a` and the source resource backend directory contains no blob binary. This makes packaged startup behavior depend on a binary name/path that does not match committed assets.

## Success Criteria

- Active packaged startup scripts start the actual committed blob/storage binary name or clearly fail with an explicit diagnostic when the binary is absent.
- Source resource and generated backend asset copies no longer disagree about the intended blob/storage binary contract.
- Targeted scans for `novaic-blob-service`, `novaic-storage-a`, and blob service startup paths show only intentional references.
- `bash -n` passes for the modified packaged startup scripts.

