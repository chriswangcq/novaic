# Classify Gateway SQLite State and Postgres Boundary

## Problem

Gateway may have a live or archived `gateway.db` containing auth, file registry, or operational state. Its tables need explicit classification before deciding whether they migrate to `novaic_gateway`, remain obsolete residue, or are owned by Entangled/other services.

This belongs under P010 because Gateway has a distinct runtime and ownership boundary from Cortex.

## Success Criteria

- The live `api` host is checked for `gateway.db` and any WAL/SHM files, including file metadata and open holders if present.
- Gateway process args and code paths that reference SQLite are identified without recording secrets.
- Gateway schema and row counts are captured if a live or archived DB exists.
- Gateway tables are classified as auth state, file/entity ops state, obsolete residue, or migration candidate.
- Future Postgres boundary and backup expectations are documented.
- No Gateway production cutover is attempted.

