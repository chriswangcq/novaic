# Cross-service semantic residue discovery and classification

## Problem

Find and classify remaining semantic residue across docs, scripts, app resources, generated assets, and service code. The goal is evidence, not patching: identify which references are active and misleading, generated copies, historical docs, intentional lower-level protocols, or harmless tests.

## Success Criteria

- Targeted scans cover service-boundary terms for Cortex, Gateway, Business, Device/devicectl, Queue, Runtime, Blob, LogicalFS, Sandboxd, shell, display, and VMuse/VmControl.
- Findings are grouped by file/surface and classified as active, stale, generated, historical, lower-level protocol, or test/fixture.
- Exact remediation candidates are listed for the next child problem.
- Broad risky areas are called out instead of silently accepted.
