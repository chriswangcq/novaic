# Sandbox LogicalFS Blob Service Call Path Map

## Problem

Map how sandbox service/core and LogicalFS interact with each other and with blob service. This child belongs under P557 because sandbox/logicalfs are the intended real-time RO/RW file authority boundary.

## Success Criteria

- Scans sandbox service, sandbox SDK, and LogicalFS imports/calls.
- Reads high-signal service/core files in bounded slices.
- Explains whether sandbox uses LogicalFS for filesystem authority and where blob is used.
- Records suspicious direct fallback paths for P553.
