# Clean stale Blob workspace ownership language

## Problem

Docs, comments, and names that say or imply Blob owns live Cortex Workspace
semantics will confuse future code generation. They must be narrowed to cheap
byte/object storage or transitional persistence-adapter language.

## Success Criteria

- Stale comments/docs around `BlobCortexStore`, `WorkspaceRegistry`, Store, and
  architecture references are updated.
- No doc claims Blob is the live `RO` / `RW` authority.
- Transitional terms are explicit where direct object APIs remain.
