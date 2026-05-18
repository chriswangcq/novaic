# App backend script and launch wiring discovery ticket

## Problem Definition

App backend scripts and launch helpers may still start stale VMuse/FastMCP/direct-media entrypoints or bypass the current shell/blob/display contract.

## Proposed Solution

Scan app scripts, package scripts, Tauri helper scripts, and backend launch configuration for VMuse, FastMCP, http server, devicectl, screenshot, Blob, Sandbox, LogicalFS, shell, artifact, and service startup references. Inspect high-signal launch scripts and classify findings.

## Acceptance Criteria

- Relevant script and launch helper files are discovered.
- High-signal startup/contract references are classified.
- Remediation candidates are listed precisely, or absence is explicitly recorded.
- No scripts or launch files are modified.

## Verification Plan

Use bounded `rg --files`, focused `rg -n -i`, and targeted `sed` slices under `novaic-app/scripts`, `novaic-app/package.json`, `novaic-app/src-tauri`, and adjacent app launch helpers.

## Risks

- Some scripts may be development-only; classification should separate shipped runtime behavior from local developer convenience scripts.

## Assumptions

- App backend script wiring is concentrated under `novaic-app/scripts`, `novaic-app/package.json`, and Tauri helper scripts.
