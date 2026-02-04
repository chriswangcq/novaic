#!/usr/bin/env python3
"""
清理所有 Runtime 相关数据，便于重新测试。

清理内容：
- agent_runtimes（所有 runtime 记录）
- pipeline_tasks（与 runtime 绑定的流水线任务）
- 可选：tq_tasks / tq_sagas 中 pending/claimed 状态（清空任务队列）

使用：
  NOVAIC_DATA_DIR=~/.novaic python scripts/cleanup_runtimes.py
  NOVAIC_DATA_DIR=~/.novaic python scripts/cleanup_runtimes.py --queue   # 同时清空 TQ 队列
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path


def get_db_path() -> Path:
    data_dir = os.environ.get("NOVAIC_DATA_DIR")
    if not data_dir:
        data_dir = os.path.expanduser("~/.novaic")
    data_dir = Path(data_dir).expanduser().resolve()
    db_path = data_dir / "novaic.db"
    if not db_path.exists():
        print(f"[cleanup] ERROR: Database not found: {db_path}")
        sys.exit(1)
    return db_path


def cleanup_runtimes(conn: sqlite3.Connection, clear_queue: bool = False) -> None:
    cur = conn.execute("SELECT COUNT(*) FROM agent_runtimes")
    runtimes_count = cur.fetchone()[0]
    cur = conn.execute("SELECT COUNT(*) FROM pipeline_tasks")
    pipeline_count = cur.fetchone()[0]

    print(f"[cleanup] agent_runtimes: {runtimes_count} rows")
    print(f"[cleanup] pipeline_tasks: {pipeline_count} rows")

    conn.execute("DELETE FROM agent_runtimes")
    conn.execute("DELETE FROM pipeline_tasks")
    print("[cleanup] Deleted all agent_runtimes and pipeline_tasks")

    if clear_queue:
        for table, status_where in [
            ("tq_tasks", "status IN ('pending', 'claimed')"),
            ("tq_sagas", "status IN ('pending', 'claimed', 'running')"),
        ]:
            try:
                cur = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {status_where}")
                n = cur.fetchone()[0]
                conn.execute(f"DELETE FROM {table} WHERE {status_where}")
                print(f"[cleanup] Deleted {n} rows from {table} (pending/claimed/running)")
            except sqlite3.OperationalError as e:
                print(f"[cleanup] Skip {table}: {e}")

    conn.commit()
    print("[cleanup] Done.")


def main():
    parser = argparse.ArgumentParser(description="Clean all runtime data for fresh test")
    parser.add_argument(
        "--queue",
        action="store_true",
        help="Also clear pending/claimed tq_tasks and tq_sagas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show counts, do not delete",
    )
    args = parser.parse_args()

    db_path = get_db_path()
    print(f"[cleanup] Using database: {db_path}")

    conn = sqlite3.connect(str(db_path))

    if args.dry_run:
        cur = conn.execute("SELECT COUNT(*) FROM agent_runtimes")
        print(f"[cleanup] (dry-run) agent_runtimes: {cur.fetchone()[0]}")
        cur = conn.execute("SELECT COUNT(*) FROM pipeline_tasks")
        print(f"[cleanup] (dry-run) pipeline_tasks: {cur.fetchone()[0]}")
        conn.close()
        return

    cleanup_runtimes(conn, clear_queue=args.queue)
    conn.close()


if __name__ == "__main__":
    main()
