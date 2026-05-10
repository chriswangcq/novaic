# Audit Payload Manifest Authority Boundaries

## Problem Definition

Payload manifest work must start with a concrete call-site and behavior audit. Without this, implementation can wire one happy path while leaving read failures, local payloads, or BlobRef-only semantics as residue.

## Proposed Solution

Perform a read-only audit of:

- `Workspace.write_payload`, `Workspace.read_payload`, and step normalization/index behavior.
- `OperationalSqliteStore` payload manifest schema/methods and current tests.
- Blob adapter put/get behavior and failure surfaces.
- Existing payload tests and docs that define or imply semantic ownership.

The audit result should classify current behavior into externalized payloads, local payloads, manifest substrate, failure semantics, and follow-on implementation boundaries.

## Acceptance Criteria

- Live write/read call sites are listed with file/function pointers.
- Existing manifest fields are compared against Phase 4 needs.
- Current missing/corrupt/blob failure behavior is documented.
- Local JSON and external Blob payload semantics are separated.
- P042/P043/P044 boundaries are validated or adjusted based on evidence.

## Verification Plan

- Use `rg`, `sed`, and targeted source reads only.
- No production code changes in this audit ticket.
- Record concrete result body with call-site map and boundary decisions.

## Risks

- The audit can become too broad if it tries to solve implementation while reading.
- Old docs may describe architecture rather than runtime reality; source code is the authority for current behavior.

## Assumptions

- `OperationalSqliteStore` payload manifest methods exist but may not be wired into live workspace payload paths.
- No backward compatibility is required for older Blob-only semantic behavior.
