# UI Display Artifact and BlobRef Rendering Boundary

## Problem

Audit UI handling of display artifacts and BlobRefs to verify images are shown through artifact/display paths rather than by rendering raw base64 tool text.

## Success Criteria

- Records exact scans for BlobRef, artifact, image, thumbnail, and display rendering in frontend code.
- Cites UI slices that show BlobRef/artifact rendering behavior.
- Classifies any base64 rendering as either intentional provider request debug or risky UI residue.
- Creates a follow-up if UI display requires raw base64 from tool text.
