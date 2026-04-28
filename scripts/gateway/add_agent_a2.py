#!/usr/bin/env python3
"""
添加 A2 的 main agent 到 Gateway DB

用法:
  NOVAIC_DATA_DIR=~/Library/Application\ Support/com.novaic.app python add_agent_a2.py

或指定 data_dir:
  python add_agent_a2.py --data-dir ~/Library/Application\ Support/com.novaic.app
"""
import argparse
import json

import sqlite3
import sys
import uuid
from pathlib import Path


def utc_now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    parser = argparse.ArgumentParser(description="Add A2 agent and main subagent to Gateway DB")
    parser.add_argument("--data-dir", help="NOVAIC_DATA_DIR (default: env or ~/Library/Application Support/com.novaic.app)")
    parser.add_argument("--name", default="A2", help="Agent display name")
    parser.add_argument("--agent-id", help="Optional: use existing agent ID instead of creating new")
    args = parser.parse_args()

    data_dir = args.data_dir
    if not data_dir:
        data_dir = str(Path.home() / "Library" / "Application Support" / "com.novaic.app")
    data_dir = Path(data_dir)
    db_path = data_dir / "gateway.db"

    if not db_path.exists():
        print(f"Error: gateway.db not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        if args.agent_id:
            agent_id = args.agent_id
            cur = conn.execute("SELECT id, name FROM agents WHERE id = ?", (agent_id,))
            row = cur.fetchone()
            if not row:
                print(f"Error: Agent {agent_id} not found")
                sys.exit(1)
            print(f"Using existing agent: {row['name']} ({agent_id})")
        else:
            agent_id = str(uuid.uuid4())
            now = utc_now_iso()
            conn.execute(
                """INSERT INTO agents (id, name, created_at, vm_config, ports, setup_complete)
                   VALUES (?, ?, ?, '{}', '{}', 0)""",
                (agent_id, args.name, now),
            )
            print(f"Created agent: {args.name} ({agent_id})")

        # 创建 main subagent (v14 格式: main-{agent_id[:8]})
        subagent_id = f"main-{agent_id[:8]}"
        now = utc_now_iso()

        cur = conn.execute(
            "SELECT subagent_id FROM subagents WHERE subagent_id = ? AND agent_id = ?",
            (subagent_id, agent_id),
        )
        if cur.fetchone():
            print(f"Main subagent already exists: {subagent_id}")
        else:
            conn.execute(
                """INSERT INTO subagents (
                    subagent_id, agent_id, type, parent_subagent_id,
                    status, wake_triggers, wake_at,
                    task, progress, result, error, timeout_at,
                    hrl, summary_lock, need_rest,
                    created_at, updated_at
                ) VALUES (?, ?, 'main', NULL, 'sleeping', '[]', NULL,
                    NULL, NULL, NULL, NULL, NULL, '[]', 0, 0, ?, ?)""",
                (subagent_id, agent_id, now, now),
            )
            print(f"Created main subagent: {subagent_id}")

        conn.commit()
        print("Done. Restart the app or refresh to see A2.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
