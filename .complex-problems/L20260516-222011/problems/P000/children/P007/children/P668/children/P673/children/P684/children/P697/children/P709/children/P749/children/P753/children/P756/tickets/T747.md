# Gateway Business Device service-code residue discovery ticket

## Problem Definition

Gateway, Business, and Device code may still contain stale comments, compatibility branches, routes, or helper names that imply Gateway owns product state, Business owns hardware execution, or Device exposes old inline media/control paths.

## Proposed Solution

Run read-only scans over `novaic-gateway`, `novaic-business`, and `novaic-device` source/tests. Classify hits and list exact remediation candidates.

## Acceptance Criteria

- Gateway/Business/Device source and tests are scanned.
- Findings are classified as current edge/domain/hardware paths, guard tests, intentional protocol code, or stale remediation candidates.
- Exact safe remediation candidates are listed.
- No Gateway/Business/Device code is modified in this discovery ticket.

## Verification Plan

Use targeted `rg` scans for gateway/business/device ownership terms, legacy/fallback/direct terms, media/screenshot/base64 terms, and route names. Spot-read suspicious files and record candidates.
