# Audit Live Code for Blob-as-Workspace Authority

## Problem

Live code may still let Blob APIs act as the authority for Cortex workspace semantics, bypassing Workspace/LogicalFS boundaries. This child should inspect runtime code paths, not broad docs.

## Success Criteria

- Scan live code under `novaic-cortex`, `novaic-agent-runtime`, `novaic-logicalfs`, `novaic-sandbox-service`, `novaic-sandbox-sdk`, and `novaic-common` for Blob/workspace authority patterns.
- Classify live matches as valid artifact/file service, durable byte store behind Workspace, or active semantic bypass.
- Remove or spawn a concrete follow-up for any active semantic bypass.
