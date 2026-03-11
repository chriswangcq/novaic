#!/bin/bash
# queue.db 深度清理 - 删除所有已完成/失败的任务和 saga，回收磁盘
# 使用前请先关闭 NovAIC app（否则 VACUUM 可能失败）
# 用法: ./scripts/cleanup_queue_db.sh [-y] [--no-vacuum]

set -e
FORCE=0
NO_VACUUM=0
for arg in "$@"; do
    [[ "$arg" == "-y" || "$arg" == "--yes" ]] && FORCE=1
    [[ "$arg" == "--no-vacuum" ]] && NO_VACUUM=1
done

DATA_DIR="${NOVAIC_DATA_DIR:-$HOME/Library/Application Support/com.novaic.app}"
Q="$DATA_DIR/queue.db"

echo "=== queue.db 深度清理 ==="
echo "数据目录: $DATA_DIR"
echo ""

if [[ ! -f "$Q" ]]; then
    echo "未找到 queue.db"
    exit 1
fi

# 检查 app 是否在运行
if [[ $FORCE -eq 0 ]] && pgrep -f "NovAIC.app" > /dev/null 2>&1; then
    echo "⚠️  检测到 NovAIC 进程，建议先完全退出 app"
    echo "    确认已退出后可加 -y 强制执行: $0 -y"
    exit 1
fi

echo "清理前:"
ls -lh "$Q"
echo ""
sqlite3 "$Q" "
SELECT 'tq_tasks' as tbl, status, count(*) FROM tq_tasks GROUP BY status;
SELECT 'tq_sagas' as tbl, status, count(*) FROM tq_sagas GROUP BY status;
SELECT 'tq_idempotency_ledger' as tbl, status, count(*) FROM tq_idempotency_ledger GROUP BY status;
" 2>/dev/null || true
echo ""

# 1. 删除 done/failed 任务（保留 pending/claimed）
N1=$(sqlite3 "$Q" "SELECT count(*) FROM tq_tasks WHERE status IN ('done','failed');" 2>/dev/null || echo 0)
sqlite3 "$Q" "DELETE FROM tq_tasks WHERE status IN ('done','failed');" 2>/dev/null || true
echo "  tq_tasks: 删除 $N1 条 (done/failed)"

# 2. 删除 completed/failed saga（保留 pending/running/launched）
N2=$(sqlite3 "$Q" "SELECT count(*) FROM tq_sagas WHERE status IN ('completed','failed');" 2>/dev/null || echo 0)
sqlite3 "$Q" "DELETE FROM tq_sagas WHERE status IN ('completed','failed');" 2>/dev/null || true
echo "  tq_sagas: 删除 $N2 条 (completed/failed)"

# 3. 删除 completed 的幂等 ledger
N3=$(sqlite3 "$Q" "SELECT count(*) FROM tq_idempotency_ledger WHERE status='completed';" 2>/dev/null || echo 0)
sqlite3 "$Q" "DELETE FROM tq_idempotency_ledger WHERE status='completed';" 2>/dev/null || true
echo "  tq_idempotency_ledger: 删除 $N3 条 (completed)"

# 4. VACUUM 回收磁盘（需要独占，app 需关闭）
if [[ $NO_VACUUM -eq 1 ]]; then
    echo ""
    echo "  跳过 VACUUM (--no-vacuum)"
else
    echo ""
    echo "  VACUUM 回收磁盘（约需等量临时空间）..."
    if sqlite3 "$Q" "VACUUM;" 2>/dev/null; then
        echo "  VACUUM 完成"
    else
        echo "  VACUUM 失败（可能 app 未关闭或磁盘不足），可加 --no-vacuum 跳过"
    fi
fi

echo ""
echo "清理后:"
ls -lh "$Q"
sqlite3 "$Q" "
SELECT 'tq_tasks' as tbl, status, count(*) FROM tq_tasks GROUP BY status;
SELECT 'tq_sagas' as tbl, status, count(*) FROM tq_sagas GROUP BY status;
SELECT 'tq_idempotency_ledger' as tbl, status, count(*) FROM tq_idempotency_ledger GROUP BY status;
" 2>/dev/null || true
echo ""
echo "=== 完成 ==="
