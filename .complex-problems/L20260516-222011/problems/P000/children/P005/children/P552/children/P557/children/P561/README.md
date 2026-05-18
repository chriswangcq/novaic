# Artifact And Display Blob Usage Map

## Problem

Separate intended cheap artifact/display blob usage from inappropriate blob-as-realtime-filesystem usage. This child belongs under P557 because blob should remain a cheap file server for artifacts, not the live RO/RW authority.

## Success Criteria

- Scans blob references across runtime, Cortex, sandbox, and docs.
- Classifies artifact/display usage versus real-time file semantics.
- Flags any blob usage that appears to proxy live RO/RW workspace state.
- Records exact commands and artifacts.
