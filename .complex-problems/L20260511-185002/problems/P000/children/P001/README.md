# Inventory shell CLI surfaces and blob-contract risks

## Problem

Before changing behavior, inventory every shell-exposed CLI command surface and classify which commands produce plain text, structured JSON, files, media, screenshots, or potentially large payloads. Identify live paths that can violate the blob artifact contract.

## Success Criteria

- `agentctl`, `cortex`, and `devicectl` shell capability command surfaces are inventoried.
- Each command is classified as text-only, structured-small, payload-inspection, file/media-producing, or proxy/raw.
- Confirmed blob-contract risks are listed with exact code pointers.
- The next repair targets are clear and bounded.
