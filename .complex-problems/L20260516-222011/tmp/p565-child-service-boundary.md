# Sandbox Service Execution Boundary Residue

## Problem

Audit `novaic-sandbox-service` for execution bypasses, local fallback paths, host path exposure, mount bypasses, or stale compatibility routes.

## Success Criteria

- Records exact scans for exec, fallback, local, host path, mount, base64, stdout/stderr, and compatibility terms.
- Cites service code/test slices.
- Runs focused sandbox service tests.
- Creates follow-up if sandboxd boundary can be bypassed in active code.
