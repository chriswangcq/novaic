#!/bin/bash
# 清理所有 DB 的陈年内容
# 使用前请先关闭 NovAIC app
# 用法: ./cleanup_all_dbs.sh [-y]  加 -y 跳过运行检测强制执行

set -e
FORCE=0
NO_VACUUM=0
for arg in "$@"; do
    [[ "$arg" == "-y" || "$arg" == "--yes" ]] && FORCE=1
    [[ "$arg" == "--no-vacuum" ]] && NO_VACUUM=1
done

DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"
KEEP_DAYS_QUEUE=3    # queue 保留最近 3 天（更激进，queue 太大）
KEEP_DAYS_CHAT=30    # chat/execution_logs 保留最近 30 天

echo "=== NovAIC DB 清理脚本 ==="
echo "数据目录: $DATA_DIR"
echo "保留策略: queue=$KEEP_DAYS_QUEUE 天, chat/logs=$KEEP_DAYS_CHAT 天"
echo "参数: -y 跳过进程检测, --no-vacuum 跳过 VACUUM(磁盘不足时用)"
echo ""

# 检查 app 是否在运行（-y 时跳过）
if [[ $FORCE -eq 0 ]] && pgrep -f "NovAIC.app" > /dev/null 2>&1; then
    echo "⚠️  检测到 NovAIC 相关进程，建议先完全退出 app"
    echo "    若确认已退出（可能是僵尸进程），可加 -y 参数强制执行: $0 -y"
    exit 1
fi

# 使用 SQLite 内置日期函数，跨平台
echo "保留: queue 最近 ${KEEP_DAYS_QUEUE} 天, chat/logs 最近 ${KEEP_DAYS_CHAT} 天"
echo ""

# --- queue.db ---
echo ">>> 清理 queue.db"
Q="$DATA_DIR/queue.db"
if [[ -f "$Q" ]]; then
    # tq_tasks: 删除 done/failed 的陈年任务 (created_at 或 finished_at 超过 N 天)
    N1=$(sqlite3 "$Q" "SELECT count(*) FROM tq_tasks WHERE status IN ('done','failed') AND (datetime(created_at) < datetime('now','-$KEEP_DAYS_QUEUE days') OR (finished_at IS NOT NULL AND datetime(finished_at) < datetime('now','-$KEEP_DAYS_QUEUE days')));" 2>/dev/null || echo 0)
    sqlite3 "$Q" "DELETE FROM tq_tasks WHERE status IN ('done','failed') AND (datetime(created_at) < datetime('now','-$KEEP_DAYS_QUEUE days') OR (finished_at IS NOT NULL AND datetime(finished_at) < datetime('now','-$KEEP_DAYS_QUEUE days')));" 2>/dev/null || true
    echo "  tq_tasks: 删除约 $N1 条"

    # tq_sagas: 删除已完成的陈年 saga
    N2=$(sqlite3 "$Q" "SELECT count(*) FROM tq_sagas WHERE status IN ('completed','failed') AND (datetime(created_at) < datetime('now','-$KEEP_DAYS_QUEUE days') OR (completed_at IS NOT NULL AND datetime(completed_at) < datetime('now','-$KEEP_DAYS_QUEUE days')));" 2>/dev/null || echo 0)
    sqlite3 "$Q" "DELETE FROM tq_sagas WHERE status IN ('completed','failed') AND (datetime(created_at) < datetime('now','-$KEEP_DAYS_QUEUE days') OR (completed_at IS NOT NULL AND datetime(completed_at) < datetime('now','-$KEEP_DAYS_QUEUE days')));" 2>/dev/null || true
    echo "  tq_sagas: 删除约 $N2 条"

    # tq_idempotency_ledger: 删除 completed 且过期的
    N3=$(sqlite3 "$Q" "SELECT count(*) FROM tq_idempotency_ledger WHERE status='completed' AND datetime(updated_at) < datetime('now','-$KEEP_DAYS_QUEUE days');" 2>/dev/null || echo 0)
    sqlite3 "$Q" "DELETE FROM tq_idempotency_ledger WHERE status='completed' AND datetime(updated_at) < datetime('now','-$KEEP_DAYS_QUEUE days');" 2>/dev/null || true
    echo "  tq_idempotency_ledger: 删除约 $N3 条"

    if [[ $NO_VACUUM -eq 1 ]]; then
        echo "  跳过 VACUUM (--no-vacuum)"
    else
        echo "  VACUUM (需约 8GB 临时空间，磁盘不足可加 --no-vacuum)..."
        if sqlite3 "$Q" "VACUUM;" 2>/dev/null; then
            echo "  VACUUM 完成"
        else
            echo "  VACUUM 失败(可能磁盘满)，可加 --no-vacuum 跳过"
        fi
    fi
else
    echo "未找到 queue.db"
fi
echo ""

# --- gateway.db ---
echo ">>> 清理 gateway.db"
G="$DATA_DIR/gateway.db"
if [[ -f "$G" ]]; then
    # chat_messages: 保留最近 KEEP_DAYS_CHAT 天
    N1=$(sqlite3 "$G" "SELECT count(*) FROM chat_messages WHERE datetime(created_at) < datetime('now','-$KEEP_DAYS_CHAT days') OR datetime(timestamp) < datetime('now','-$KEEP_DAYS_CHAT days');" 2>/dev/null || echo 0)
    sqlite3 "$G" "DELETE FROM chat_messages WHERE datetime(created_at) < datetime('now','-$KEEP_DAYS_CHAT days') OR datetime(timestamp) < datetime('now','-$KEEP_DAYS_CHAT days');" 2>/dev/null || true
    echo "  chat_messages: 删除约 $N1 条"

    # execution_logs
    N2=$(sqlite3 "$G" "SELECT count(*) FROM execution_logs WHERE datetime(timestamp) < datetime('now','-$KEEP_DAYS_CHAT days');" 2>/dev/null || echo 0)
    sqlite3 "$G" "DELETE FROM execution_logs WHERE datetime(timestamp) < datetime('now','-$KEEP_DAYS_CHAT days');" 2>/dev/null || true
    echo "  execution_logs: 删除约 $N2 条"

    [[ $NO_VACUUM -eq 0 ]] && sqlite3 "$G" "VACUUM;" 2>/dev/null && echo "  VACUUM 完成" || true
else
    echo "未找到 gateway.db"
fi
echo ""

echo "=== 清理完成 ==="
echo "当前 DB 大小:"
ls -lh "$DATA_DIR"/*.db 2>/dev/null || true
