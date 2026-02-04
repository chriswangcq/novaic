#!/usr/bin/env python3
"""
批量迁移到 FIFO 锁

将所有数据库操作迁移到使用 FIFO 锁
"""

import re
import os
from pathlib import Path

# 要更新的文件列表
FILES_TO_UPDATE = [
    "novaic-backend/gateway/api/internal.py",
    "novaic-backend/gateway/api/routes.py",
    "novaic-backend/task_queue/routes.py",
]

BASE_DIR = Path("/Users/wangchaoqun/novaic")


def detect_lock_type_and_resource(code_block: str) -> tuple:
    """
    根据代码块检测应该使用的锁类型和资源 ID
    
    Returns:
        (lock_type, resource_id_var, timeout)
    """
    code_lower = code_block.lower()
    
    # Message 相关
    if 'chat_messages' in code_lower:
        if 'message_id' in code_block:
            return ('message', 'message_id', 10.0)
        elif 'agent_id' in code_block:
            return ('agent', 'agent_id', 10.0)
    
    # Agent/SubAgent 相关
    if 'subagents' in code_lower or 'agent_runtimes' in code_lower:
        if 'agent_id' in code_block:
            return ('agent', 'agent_id', 10.0)
        elif 'runtime_id' in code_block:
            # 需要先从 runtime_id 解析 agent_id
            return ('agent', 'agent_id', 10.0)
    
    # Task 相关
    if 'tq_tasks' in code_lower:
        if 'task_id' in code_block:
            return ('task', 'task_id', 10.0)
    
    # Saga 相关
    if 'tq_sagas' in code_lower:
        if 'saga_id' in code_block:
            return ('saga', 'saga_id', 10.0)
    
    # 跨表操作或无法确定 → 全局锁
    return ('global', None, 15.0)


def update_file(file_path: Path):
    """更新单个文件"""
    print(f"\n{'='*60}")
    print(f"更新文件: {file_path.relative_to(BASE_DIR)}")
    print('='*60)
    
    content = file_path.read_text()
    original_content = content
    updates = 0
    
    # 模式 1: with db.get_connection() as conn:
    pattern1 = r'with db\.get_connection\(\) as conn:'
    matches1 = list(re.finditer(pattern1, content))
    
    for match in reversed(matches1):  # 从后往前替换，避免位置变化
        start = match.start()
        end = match.end()
        
        # 提取上下文（后面 500 个字符）
        context = content[start:min(start + 500, len(content))]
        
        # 检测锁类型
        lock_type, resource_var, timeout = detect_lock_type_and_resource(context)
        
        # 构造新代码
        if resource_var and resource_var in context[:200]:
            new_code = f'with db.get_connection("{lock_type}", resource_id={resource_var}, timeout={timeout}) as conn:'
        else:
            new_code = f'with db.get_connection("{lock_type}", timeout={timeout}) as conn:'
        
        print(f"  [{updates+1}] 第 {content[:start].count(chr(10))+1} 行:")
        print(f"    旧: {match.group()}")
        print(f"    新: {new_code}")
        
        content = content[:start] + new_code + content[end:]
        updates += 1
    
    # 模式 2: with db.transaction():
    pattern2 = r'with db\.transaction\(\):'
    matches2 = list(re.finditer(pattern2, content))
    
    for match in reversed(matches2):
        start = match.start()
        end = match.end()
        
        # 提取上下文
        context = content[start:min(start + 500, len(content))]
        
        # 检测锁类型
        lock_type, resource_var, timeout = detect_lock_type_and_resource(context)
        
        # 构造新代码
        if resource_var and resource_var in context[:200]:
            new_code = f'with db.transaction("{lock_type}", resource_id={resource_var}, timeout={timeout}):'
        else:
            new_code = f'with db.transaction("{lock_type}", timeout={timeout}):'
        
        print(f"  [{updates+1}] 第 {content[:start].count(chr(10))+1} 行:")
        print(f"    旧: {match.group()}")
        print(f"    新: {new_code}")
        
        content = content[:start] + new_code + content[end:]
        updates += 1
    
    if updates > 0:
        # 备份原文件
        backup_path = file_path.with_suffix('.py.bak')
        backup_path.write_text(original_content)
        print(f"\n  ✅ 已备份到: {backup_path.name}")
        
        # 写入新内容
        file_path.write_text(content)
        print(f"  ✅ 已更新 {updates} 处锁")
    else:
        print("  ⏭️  无需更新")
    
    return updates


def main():
    print("=" * 60)
    print("开始迁移到 FIFO 锁...")
    print("=" * 60)
    
    total_updates = 0
    
    for file_rel in FILES_TO_UPDATE:
        file_path = BASE_DIR / file_rel
        if file_path.exists():
            updates = update_file(file_path)
            total_updates += updates
        else:
            print(f"⚠️  文件不存在: {file_rel}")
    
    print("\n" + "=" * 60)
    print(f"✅ 迁移完成！共更新 {total_updates} 处锁")
    print("=" * 60)
    print("\n下一步:")
    print("1. 检查更新的文件")
    print("2. 运行测试")
    print("3. 如有问题，可从 .bak 文件恢复")


if __name__ == "__main__":
    main()
