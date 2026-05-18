# Sandbox Mount Ownership and Bypass Residue

## Problem

Classify mount/source_root/stable_cwd handling across SDK DTOs, Cortex LogicalFS planning, and sandbox-service mount namespace internals to confirm mount ownership is layered and clients cannot bypass sandboxd.

## Success Criteria

- Records exact scans for mount/source_root/stable_cwd/bind/namespace/host path terms.
- Cites SDK DTO, Cortex LogicalFS mount plan, and sandbox-service mount namespace slices.
- Classifies each hit as DTO, Cortex planning, service-internal, test fixture, or risky bypass.
- Runs focused sandboxd/logicalfs/mount tests.
- Creates follow-up if client-side mount bypass remains.
