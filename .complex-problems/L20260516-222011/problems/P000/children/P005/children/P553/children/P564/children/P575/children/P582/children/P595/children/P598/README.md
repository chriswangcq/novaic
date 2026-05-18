# Display Handler Durable ImageRef Test Coverage

## Problem

Verify the runtime display handler durable payload is protected by tests that store BlobRef `image_ref` metadata and omit inline image `data`.

## Success Criteria

- Records exact scans for display handler durable payload tests.
- Cites tests proving display public output replaces images with placeholders and durable payload stores `image_ref`.
- Cites tests proving durable payload does not depend on inline base64 data.
- Creates a concrete follow-up if display durable coverage is missing.
