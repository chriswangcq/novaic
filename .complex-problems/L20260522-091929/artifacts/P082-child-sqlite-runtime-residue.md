# Isolate Session And Outbox SQLite Runtime Residue

## Problem

The Postgres cutover should not leave session/outbox runtime behavior depending on stale local SQLite database paths, implicit fallback construction, or SQLite SQL embedded in queue business code. SQLite can remain as a bounded adapter/test fixture during transition, but production session/outbox paths should make the Postgres boundary explicit.

## Success Criteria

- Session/outbox production wiring does not create or select stale local `.db` paths when Postgres configuration is expected.
- SQLite-specific path handling is confined to explicit SQLite adapter, migration, archive, or test-fixture code.
- Queue session/outbox business modules do not branch on local SQLite filenames or environment fallback paths.
- Grep/audit artifacts identify remaining SQLite references and classify each as adapter/test/migration residue or removed runtime residue.
- Tests or static guards cover the most important no-runtime-sqlite-path assumptions for session/outbox code.
- The final result documents any intentionally retained SQLite adapter boundary so future cleanup does not have to rediscover it.
