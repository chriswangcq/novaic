#!/usr/bin/env python3
"""
数据库迁移脚本：agent_index → ports

将旧的 agent_index 字段转换为持久化的 ports 配置。
此脚本应在重构后首次启动前运行一次。

使用方法：
    python novaic-backend/scripts/migrate_agent_index_to_ports.py [--dry-run] [--data-dir DIR]

选项：
    --dry-run         只显示迁移计划，不实际修改数据库
    --data-dir DIR    指定数据目录（默认：~/.local/share/novaic-gateway）
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from gateway.config.agents_db import allocate_ports_for_agent
from gateway.db.repositories.agent import AgentRepository
from gateway.db.access import get_db


def setup_environment(data_dir: str = None):
    """设置环境变量"""
    if data_dir is None:
        # 尝试从环境变量获取
        data_dir = os.environ.get("NOVAIC_DATA_DIR")
        
        # 如果环境变量也没有，使用默认路径
        if data_dir is None:
            data_dir = str(Path.home() / ".local" / "share" / "novaic-gateway")
    
    # 设置环境变量
    os.environ["NOVAIC_DATA_DIR"] = data_dir
    
    # 确保数据目录存在
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    return data_dir


def migrate_agent_index_to_ports(dry_run: bool = False, data_dir: str = None) -> int:
    """迁移所有 agent 的 agent_index 到 ports
    
    Args:
        dry_run: 如果为 True，只显示迁移计划，不实际修改数据库
        data_dir: 数据目录路径
        
    Returns:
        错误数量（0 表示成功）
    """
    
    # 设置环境变量
    data_dir = setup_environment(data_dir)
    
    print("=" * 60)
    print("Agent Index → Ports Migration Script")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print()
    
    if dry_run:
        print("\n[DRY RUN MODE] - No changes will be made\n")
    
    # 初始化数据库和 repository
    db = get_db()
    repo = AgentRepository(db)
    
    # 获取所有 agent
    all_agents = repo.list_agents()
    
    if not all_agents:
        print("✅ No agents found in database")
        return 0
    
    print(f"Found {len(all_agents)} agents\n")
    
    # 统计
    needs_migration = []
    already_migrated = []
    
    # 分析每个 agent
    for agent_data in all_agents:
        agent_id = agent_data.get("id")
        agent_name = agent_data.get("name", "Unknown")
        vm_config = agent_data.get("vm_config", {})
        ports = agent_data.get("ports", {})
        
        has_agent_index = "agent_index" in vm_config
        has_ports = ports and any(ports.values())  # 检查是否有非空端口配置
        
        if has_agent_index and not has_ports:
            needs_migration.append({
                "id": agent_id,
                "name": agent_name,
                "agent_index": vm_config["agent_index"],
                "vm_config": vm_config,
                "ports": ports
            })
        elif has_ports:
            already_migrated.append({
                "id": agent_id,
                "name": agent_name
            })
    
    # 显示统计
    print(f"✅ Already migrated: {len(already_migrated)}")
    print(f"⏳ Needs migration:  {len(needs_migration)}")
    print()
    
    if not needs_migration:
        print("✅ All agents are already up to date!")
        return 0
    
    # 显示迁移计划
    print("Migration Plan:")
    print("-" * 60)
    for agent in needs_migration:
        agent_index = agent["agent_index"]
        ports = allocate_ports_for_agent(agent_index)
        print(f"  {agent['name']} (ID: {agent['id'][:8]}...)")
        print(f"    agent_index: {agent_index}")
        print(f"    → vm:       {ports.vm}")
        print(f"    → session:  {ports.session}")
        print(f"    → local:    {ports.local}")
        print(f"    → memory:   {ports.memory}")
        print(f"    → chat:     {ports.chat}")
        print(f"    → qemudebug: {ports.qemudebug}")
        print(f"    → vnc:      {ports.vnc}")
        print(f"    → websocket: {ports.websocket}")
        print(f"    → ssh:      {ports.ssh}")
        print()
    
    if dry_run:
        print("[DRY RUN] Migration not executed. Remove --dry-run to apply changes.")
        return 0
    
    # 执行迁移
    print("Executing migration...")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for agent in needs_migration:
        agent_id = agent["id"]
        agent_name = agent["name"]
        agent_index = agent["agent_index"]
        vm_config = agent["vm_config"].copy()
        
        try:
            # 计算端口
            ports = allocate_ports_for_agent(agent_index)
            ports_dict = {
                "vm": ports.vm,
                "session": ports.session,
                "local": ports.local,
                "memory": ports.memory,
                "chat": ports.chat,
                "qemudebug": ports.qemudebug,
                "vnc": ports.vnc,
                "websocket": ports.websocket,
                "ssh": ports.ssh,
            }
            
            # 删除 agent_index
            if "agent_index" in vm_config:
                del vm_config["agent_index"]
            
            # 更新数据库
            repo.update_agent(
                agent_id=agent_id,
                vm_config=vm_config,
                ports=ports_dict
            )
            
            print(f"✅ Migrated: {agent_name}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to migrate {agent_name}: {e}")
            error_count += 1
    
    # 总结
    print()
    print("=" * 60)
    print("Migration Complete")
    print("=" * 60)
    print(f"✅ Successfully migrated: {success_count}")
    if error_count > 0:
        print(f"❌ Failed:               {error_count}")
    print()
    
    return error_count


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate agent_index to ports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration plan (using default data directory)
  python novaic-backend/scripts/migrate_agent_index_to_ports.py --dry-run
  
  # Execute migration (using default data directory)
  python novaic-backend/scripts/migrate_agent_index_to_ports.py
  
  # Use custom data directory
  python novaic-backend/scripts/migrate_agent_index_to_ports.py --data-dir /path/to/data
  
  # Use environment variable
  NOVAIC_DATA_DIR=/path/to/data python novaic-backend/scripts/migrate_agent_index_to_ports.py
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show migration plan without making changes"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Data directory path (default: ~/.local/share/novaic-gateway or $NOVAIC_DATA_DIR)"
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = migrate_agent_index_to_ports(
            dry_run=args.dry_run,
            data_dir=args.data_dir
        )
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
