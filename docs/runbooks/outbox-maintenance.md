# Outbox Maintenance Runbook

The Dispatch Subscriber pattern relies on the `message_outbox` table in Entangled. Over time, delivered messages will accumulate and consume disk space.

## Compaction

A script is provided to compact the outbox table by deleting delivered messages that are older than a specific retention period.

```bash
# Delete delivered messages older than 7 days (default)
./scripts/outbox-compact.sh

# Specify a custom retention period (e.g. 3 days)
./scripts/outbox-compact.sh 3
```

This should be run periodically via cron or a scheduler to keep the Entangled database size manageable.

## Poison Messages (DLQ)

Messages that encounter permanent errors (like `no_owner`, `bad_argument`) or have exhausted their retries (default 5 `attempts`) will remain in the table with `delivered_at = NULL` and a high `attempts` count. They will not be repeatedly claimed due to the `attempts < max_attempts` query constraint.

To view these orphan messages:

```sql
sqlite3 ~/.novaic/data/entangled.db "SELECT id, trigger_type, attempts, last_error FROM message_outbox WHERE delivered_at IS NULL AND attempts >= 5;"
```
