# Device/devicectl surface discovery and contract map

## Problem

Discover Device service, devicectl CLI commands, launch references, and host-device capture/control surfaces. This belongs under P708 because remediation needs an evidence-backed map of which layer owns hardware control and which layer only exposes shell-facing commands.

## Success Criteria

- Device service entrypoints and launch references are listed with evidence.
- devicectl command surfaces, especially HD screenshot/capture, are listed with evidence.
- Hardware/control responsibilities are separated from Blob, display, Cortex, Runtime, and shell output projection.
- Cleanup candidates are listed for the remediation child.
