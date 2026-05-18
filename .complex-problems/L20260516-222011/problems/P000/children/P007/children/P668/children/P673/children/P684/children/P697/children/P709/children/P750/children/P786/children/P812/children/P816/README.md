# Child Problem: Factory logs rendering inventory

## Problem

Before editing `factory-logs.html`, map every raw request/response/message/tool rendering entrypoint so the scrub layer is not attached to only one tab while another tab keeps leaking raw payloads.

## Success Criteria

- Inventory lists all relevant rendering functions and the raw values they render.
- Each rendering entrypoint is assigned to either safe metadata, projected payload, or removed.
- The inventory identifies the minimal helper shape needed for implementation.
