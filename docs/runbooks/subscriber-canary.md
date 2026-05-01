# Retired Runbook: Subscriber Canary

> Archived 2026-05-01. The subscriber canary path no longer exists.

`DispatchSubscriber` is now a required process in the normal agent loop. It is
started by `scripts/start.sh` / deployment scripts and is not controlled by a
runtime switch.

Current operational checks:

```bash
ps aux | rg 'main_subscriber.py'
rg 'DispatchSubscriber|message_outbox|ERROR|Traceback' /opt/novaic/data/logs/business-*.log
sqlite3 /opt/novaic/data/entangled.db \
  "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM message_outbox WHERE delivered_at IS NULL;"
```

If `message_outbox` stops draining, treat it as a required-process incident:
restart the backend stack and inspect `main_subscriber.py` / Business logs. Do
not look for a canary flag or a disabled subscriber mode.
