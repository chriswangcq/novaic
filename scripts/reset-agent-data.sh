#!/bin/bash
# Reset all agent runtime data for a clean test run.
#
# Preserves: users, refresh_tokens, ssh_keys, config, pc_clients, vm_processes
# Wipes:    sessions, session_messages, pipeline_tasks,
#           all tq_* queue tables, Redis cortex:lock:* keys,
#           OSS users/* prefix, local Cortex data dir.
#
# Run on the server: bash /opt/novaic/reset-agent-data.sh
set -euo pipefail

GW_DB="/opt/novaic/data/gateway.db"
QU_DB="/opt/novaic/data/queue.db"

echo "=== 1. Stop services ==="
bash /opt/novaic/start.sh --stop || true
sleep 2

echo "=== 2. Clean Gateway agent data (keep users/auth/config) ==="
sqlite3 "$GW_DB" << 'SQL'
DELETE FROM session_messages;
DELETE FROM sessions;
DELETE FROM pipeline_tasks;
DELETE FROM entangled_sync_versions;
SELECT 'Gateway: sessions=' || (SELECT count(*) FROM sessions)
    || ' messages=' || (SELECT count(*) FROM session_messages)
    || ' pipeline_tasks=' || (SELECT count(*) FROM pipeline_tasks)
    || ' users=' || (SELECT count(*) FROM users) || ' (preserved)';
SQL

echo "=== 3. Clean Queue DB ==="
sqlite3 "$QU_DB" << 'SQL'
DELETE FROM tq_tasks;
DELETE FROM tq_sagas;
DELETE FROM tq_idempotency_ledger;
DELETE FROM tq_active_sessions;
DELETE FROM tq_pending_triggers;
SELECT 'Queue: tasks=' || (SELECT count(*) FROM tq_tasks)
    || ' sagas=' || (SELECT count(*) FROM tq_sagas)
    || ' active_sessions=' || (SELECT count(*) FROM tq_active_sessions)
    || ' pending_triggers=' || (SELECT count(*) FROM tq_pending_triggers);
SQL

echo "=== 4. Clean Redis scope locks ==="
# P3-6: Cortex uses Redis for distributed scope locks
# (``cortex:lock:{user}:{agent}:{scope}``). After stopping services in
# step 1 there should be nothing held, but flush anyway so tests start
# from a pristine state instead of waiting for the 300s TTL.
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    flushed=$(redis-cli --no-raw eval "
        local keys = redis.call('keys', ARGV[1])
        for i=1,#keys,500 do
            redis.call('del', unpack(keys, i, math.min(i+499, #keys)))
        end
        return #keys
    " 0 'cortex:lock:*')
    echo "  Redis: deleted ${flushed} cortex:lock:* keys (DBSIZE=$(redis-cli DBSIZE))."
else
    echo "  Redis: redis-cli unavailable or server down — Cortex will refuse to start."
fi

echo "=== 5. Clean OSS agent data (users/*) ==="
# shellcheck disable=SC1091
source /opt/novaic/cortex_oss.env
# Activate Cortex venv for boto3.
# shellcheck disable=SC1091
source /opt/novaic/services/novaic-cortex/.venv/bin/activate
python3 << 'PYEOF'
import boto3, os
from botocore.config import Config

s3 = boto3.client("s3",
    endpoint_url="https://oss-cn-hongkong.aliyuncs.com",
    region_name="cn-hongkong",
    aws_access_key_id=os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"],
    config=Config(s3={"addressing_style": "virtual"}))

BUCKET = "novaic-s3-bucket"
PREFIX = "users/"
# Alibaba OSS's DeleteObjects requires a signed Content-MD5 which boto3
# doesn't compute by default → use per-object delete_object instead.
deleted = 0
for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX):
    for o in page.get("Contents") or []:
        s3.delete_object(Bucket=BUCKET, Key=o["Key"])
        deleted += 1
print(f"  OSS: deleted {deleted} objects under {PREFIX}")
PYEOF

echo "=== 6. Clean local Cortex data ==="
rm -rf /opt/novaic/data/cortex/*
echo "  /opt/novaic/data/cortex/ is now empty."

echo "=== 7. Restart services ==="
bash /opt/novaic/start.sh

echo ""
echo "=== Done! All agent runtime data cleared. ==="
