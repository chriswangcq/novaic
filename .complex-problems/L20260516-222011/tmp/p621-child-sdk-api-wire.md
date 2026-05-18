# Sandbox SDK API and Wire Boundary Residue

## Problem

Audit `novaic-sandbox-sdk` production code for execution/session APIs, local fallback, subprocess/process execution, host path/mount manipulation, and base64 stdout/stderr wire decoding.

## Success Criteria

- Records exact scans over `novaic-sandbox-sdk` for subprocess/process/local/fallback/host/mount/base64/stdout/stderr/compat terms.
- Cites source slices for the public client API and any wire encode/decode handling.
- Classifies each hit as intended SDK wire handling, test fixture, risky fallback, or removable residue.
- Creates a remediation follow-up if SDK exposes active local execution or public byte leakage.
