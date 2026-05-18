# VMuse source FastMCP removal

## Problem
Delete stale FastMCP source entry code and package metadata from source VMuse while preserving the current HTTP/blob tool-output entry path.

## Success Criteria
- Source VMuse no longer imports or exposes FastMCP direct-media entry code.
- Package metadata and CLI wording point at the current HTTP/server contract.
- Existing unrelated user changes in VMuse are preserved.
