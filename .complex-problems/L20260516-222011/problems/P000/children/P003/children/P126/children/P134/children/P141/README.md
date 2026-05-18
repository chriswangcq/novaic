# Workspace payload store and blob externalization map

## Problem

Workspace payload write/read is the durable retrieval path for large tool outputs. It must keep full payloads out of normal context while preserving explicit readback through payload references.

## Success Criteria

- `write_payload` and `read_payload` behavior is mapped with source pointers.
- Local JSON versus external blob records are classified and tested.
- Payload manifests are verified to include source ref, stable step ref, size, hash, status, and retention class.
- Missing/corrupt/mismatch/blob-failure read paths are tested or split for follow-up.
