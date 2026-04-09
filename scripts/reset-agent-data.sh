#!/bin/bash
# Reset all agent history data for a clean Cortex-only start.
# Run on the server: bash /opt/novaic/services/scripts/reset-agent-data.sh
set -euo pipefail

GW_DB="/opt/novaic/data/gateway.db"
QU_DB="/opt/novaic/data/queue.db"

echo "=== 1. Stop services ==="
bash /opt/novaic/start.sh --stop || true
sleep 2

echo "=== 2. Clean Gateway DB ==="
sqlite3 "$GW_DB" << 'SQL'
DELETE FROM chat_messages;
DELETE FROM subagent_context;
DELETE FROM session_messages;
DELETE FROM sessions;
DELETE FROM execution_logs;
DELETE FROM execution_log_payloads;
DELETE FROM agent_task_history;
DELETE FROM agent_tasks;
DELETE FROM agent_notebook;
DELETE FROM agent_memory;
DELETE FROM agent_state;
DELETE FROM agent_drive;
DELETE FROM pending_questions;
DELETE FROM question_responses;

-- Delete all sub-agents, keep only main ones
DELETE FROM subagents WHERE type = 'sub';

-- Reset main subagents to clean sleeping state
UPDATE subagents SET
    status = 'sleeping',
    current_scope_id = NULL,
    wake_triggers = '[{"type": "user_response"}]',
    handoff_notes = NULL,
    wake_at = NULL,
    need_rest = 0,
    tool_ports = NULL,
    log_count = 0;

SELECT 'Gateway: agents=' || (SELECT count(*) FROM agents)
    || ' subagents=' || (SELECT count(*) FROM subagents)
    || ' chat_messages=' || (SELECT count(*) FROM chat_messages)
    || ' context=' || (SELECT count(*) FROM subagent_context);
SQL
echo "  Gateway DB cleaned."

echo "=== 3. Clean Queue DB ==="
sqlite3 "$QU_DB" << 'SQL'
DELETE FROM tq_tasks;
DELETE FROM tq_sagas;
DELETE FROM tq_idempotency_ledger;
SELECT 'Queue: tasks=' || (SELECT count(*) FROM tq_tasks)
    || ' sagas=' || (SELECT count(*) FROM tq_sagas);
SQL
echo "  Queue DB cleaned."

echo "=== 4. Clean OSS agent data ==="
source /opt/novaic/cortex_oss.env
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
prefix = "users/"
deleted = 0

paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
    objects = page.get("Contents", [])
    if not objects:
        continue
    batch = [{"Key": o["Key"]} for o in objects]
    s3.delete_objects(Bucket=BUCKET, Delete={"Objects": batch})
    deleted += len(batch)

print(f"  OSS: deleted {deleted} objects under {prefix}")
PYEOF

echo "=== 5. Clean local Cortex data ==="
rm -rf /opt/novaic/data/cortex/*
echo "  Local Cortex data cleaned."

echo "=== 6. Restart services ==="
bash /opt/novaic/start.sh
echo ""
echo "=== Done! All agent history cleared. ==="
