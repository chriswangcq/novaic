#!/bin/bash
# 恢复 Agent Loop - 解决发消息无反应、定时唤醒失效
# 根因：1) Watchdog 创建 Saga 时 Connection reset by peer
#       2) 5476 条 SYSTEM_WAKE 积压，用户消息排在后面
#       3) 4 个 message_process saga 卡在 running

set -e
DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"

echo "=== Novaic Agent Loop 恢复脚本 ==="
echo "Data dir: $DATA_DIR"
echo ""

# 1. 标记 4 个卡住的 message_process 为 failed
echo "[1/3] 清理卡住的 message_process saga..."
sqlite3 "$DATA_DIR/queue.db" "
UPDATE tq_sagas 
SET status='failed', error='Manual reset: stuck since 2026-03-04, recovery script'
WHERE id IN ('saga-a639b8fa7fed','saga-5be23972333c','saga-06ce5c374190','saga-d05a4cb68009')
AND status='running';
"
echo "   Done."

# 2. 删除积压的 SYSTEM_WAKE（保留 USER_MESSAGE），让用户消息能被处理
echo "[2/3] 清理 SYSTEM_WAKE 积压（5476 条），保留 USER_MESSAGE..."
BEFORE=$(sqlite3 "$DATA_DIR/gateway.db" "SELECT count(*) FROM chat_messages WHERE status='sending';")
sqlite3 "$DATA_DIR/gateway.db" "
DELETE FROM chat_messages 
WHERE type='SYSTEM_WAKE' AND status='sending';
"
AFTER=$(sqlite3 "$DATA_DIR/gateway.db" "SELECT count(*) FROM chat_messages WHERE status='sending';")
echo "   sending 消息: $BEFORE -> $AFTER"

# 3. 更新 subagents 的 wake_at，避免 Scheduler 继续疯狂注入
echo "[3/3] 更新 wake_at 为 30 分钟后，避免立即再次注入..."
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S.000000+00:00")
sqlite3 "$DATA_DIR/gateway.db" "
UPDATE subagents 
SET wake_at = datetime('$NOW', '+30 minutes')
WHERE status='sleeping' AND type='main' AND wake_at IS NOT NULL;
"
echo "   Done."

echo ""
echo "=== 恢复完成 ==="
echo ""
echo "请重启 NovAIC 应用以清除连接状态："
echo "  1. 完全退出 NovAIC（Cmd+Q）"
echo "  2. 重新打开 NovAIC"
echo ""
echo "重启后，你的消息应能被处理。若仍有问题，检查："
echo "  - tail -f \"$DATA_DIR/logs/watchdog-$(date +%Y%m%d).log\""
echo "  - tail -f \"$DATA_DIR/logs/queue-service.log\""
