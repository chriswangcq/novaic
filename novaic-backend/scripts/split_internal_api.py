#!/usr/bin/env python3
"""
自动拆分 gateway/api/internal.py 文件

用法:
    python scripts/split_internal_api.py

功能:
    1. 读取 internal.py
    2. 按模块拆分到 internal/ 目录
    3. 创建 __init__.py 统一导出
    4. 备份原文件为 internal.py.backup
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict

# 项目根目录（脚本在 novaic-backend/scripts/，所以 parent.parent 是 novaic-backend）
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent  # novaic-backend
INTERNAL_FILE = PROJECT_ROOT / "gateway" / "api" / "internal.py"
INTERNAL_DIR = PROJECT_ROOT / "gateway" / "api" / "internal"

# 模块定义：模块名 -> (开始标记, 结束标记, 文件名)
MODULES = {
    "helpers": {
        "start": r"# ==================== Runtime Resolution Helper ====================",
        "end": r"# ==================== SubAgent Operations",
        "file": "helpers.py",
        "imports": True,  # 需要导入部分
    },
    "subagent": {
        "start": r"# ==================== SubAgent Operations",
        "end": r"# ==================== HRL and Summary Lock Operations",
        "file": "subagent.py",
    },
    "hrl": {
        "start": r"# ==================== HRL and Summary Lock Operations",
        "end": r"# ==================== Runtime Operations",
        "file": "subagent.py",  # 合并到 subagent.py
    },
    "runtime": {
        "start": r"# ==================== Runtime Operations",
        "end": r"# ==================== Message Operations",
        "file": "runtime.py",
    },
    "message": {
        "start": r"# ==================== Message Operations",
        "end": r"# ==================== Agent Operations",
        "file": "message.py",
    },
    "agent": {
        "start": r"# ==================== Agent Operations",
        "end": r"# ==================== SSE Broadcast",
        "file": "agent.py",
    },
    "broadcast": {
        "start": r"# ==================== SSE Broadcast",
        "end": r"# ==================== Config",
        "file": "broadcast.py",
    },
    "config": {
        "start": r"# ==================== Config",
        "end": r"# ==================== LLM Operations",
        "file": "config.py",
    },
    "llm": {
        "start": r"# ==================== LLM Operations",
        "end": r"# ==================== Helpers",
        "file": "llm.py",
    },
    "helpers_dict": {
        "start": r"# ==================== Helpers",
        "end": r"# ==================== MCP Gateway Proxy",
        "file": "helpers.py",  # 合并到 helpers.py
    },
    "health": {
        "start": r"# ==================== Health Monitor Operations \(v18\)",
        "end": r"# ==================== TaskManager API",
        "file": "health.py",
    },
    "task": {
        "start": r"# ==================== TaskManager API",
        "end": r"# ==================== SSH Key API",
        "file": "task.py",
    },
    "vm": {
        "start": r"# ==================== SSH Key API",
        "end": r"# ==================== Runtime Tools API",
        "file": "vm.py",
    },
    "runtime_tools": {
        "start": r"# ==================== Runtime Tools API",
        "end": r"# ==================== Web API",
        "file": "runtime.py",  # 合并到 runtime.py
    },
    "web": {
        "start": r"# ==================== Web API",
        "end": r"# ==================== Runtime-First API",
        "file": "web.py",
    },
    "runtime_first": {
        "start": r"# ==================== Runtime-First API",
        "end": r"# ---------- VM Tools Discovery API",
        "file": "runtime.py",  # 合并到 runtime.py
    },
    "vm_tools": {
        "start": r"# ---------- VM Tools Discovery API",
        "end": None,  # 文件末尾
        "file": "vm.py",  # 合并到 vm.py
    },
}

# 基础导入（所有文件都需要）
BASE_IMPORTS = """from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

from common.enums import RuntimeStatus, SubagentStatus
from common.config import ServiceConfig
from gateway.db.access import get_db
"""

# helpers.py 需要额外导入
HELPERS_IMPORTS = BASE_IMPORTS

# 其他文件需要从 helpers 导入
OTHER_IMPORTS_TEMPLATE = """from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json

from common.enums import RuntimeStatus, SubagentStatus
from common.config import ServiceConfig
from gateway.db.access import get_db
from .helpers import resolve_runtime_ids, get_runtime_context, _runtime_to_dict, _subagent_to_dict
"""


def read_file_content(file_path: Path) -> str:
    """读取文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def find_module_boundaries(content: str) -> Dict[str, Tuple[int, int]]:
    """找到每个模块的边界（行号）"""
    lines = content.split('\n')
    boundaries = {}
    
    for module_name, module_def in MODULES.items():
        start_pattern = module_def["start"]
        end_pattern = module_def.get("end")
        
        start_idx = None
        end_idx = None
        
        # 找到开始位置
        for i, line in enumerate(lines):
            if re.search(start_pattern, line):
                start_idx = i
                break
        
        # 找到结束位置
        if end_pattern:
            search_start = start_idx + 1 if start_idx is not None else 0
            for i, line in enumerate(lines[search_start:], search_start):
                if re.search(end_pattern, line):
                    end_idx = i
                    break
        
        if start_idx is not None:
            boundaries[module_name] = (start_idx, end_idx if end_idx else len(lines))
    
    return boundaries


def extract_module_content(content: str, start_line: int, end_line: int) -> str:
    """提取模块内容"""
    lines = content.split('\n')
    return '\n'.join(lines[start_line:end_line])


def create_router_declaration(file_name: str) -> str:
    """创建 router 声明"""
    if file_name == "helpers.py":
        # helpers.py 不需要 router
        return ""
    return "\nrouter = APIRouter(prefix=\"/internal\", tags=[\"internal\"])\n"


def write_module_file(file_path: Path, content: str, file_name: str, is_helpers: bool = False):
    """写入模块文件"""
    # 添加文件头注释
    header = f'''"""
Internal API module: {file_name.replace('.py', '')}

Auto-generated by split_internal_api.py
"""

'''
    
    # 添加导入
    if is_helpers:
        imports = HELPERS_IMPORTS
    else:
        imports = OTHER_IMPORTS_TEMPLATE
    
    # 添加 router 声明（helpers.py 不需要）
    router_decl = create_router_declaration(file_name) if not is_helpers else ""
    
    # 组合内容
    full_content = header + imports + router_decl + "\n" + content.strip() + "\n"
    
    # 如果是 helpers.py，确保导出函数
    if is_helpers:
        # helpers.py 不需要 router，但需要确保函数可导出
        # 检查是否包含这些函数
        if "def resolve_runtime_ids" in content:
            full_content += "\n# Exported functions\n"
            full_content += "__all__ = ['resolve_runtime_ids', 'get_runtime_context', '_runtime_to_dict', '_subagent_to_dict']\n"
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"✓ 创建文件: {file_path}")


def create_init_file(module_files: Dict[str, str]):
    """创建 __init__.py"""
    init_content = '''"""
Internal API - Unified router

Auto-generated by split_internal_api.py
"""

from fastapi import APIRouter

'''
    
    # 收集所有唯一的文件（去重）
    unique_files = set()
    for module_name, file_name in module_files.items():
        if file_name != "helpers.py":  # helpers.py 没有 router
            unique_files.add(file_name)
    
    # 导入所有 router（每个文件只导入一次）
    routers = []
    for file_name in sorted(unique_files):
        var_name = file_name.replace('.py', '').replace('-', '_')
        init_content += f"from .{var_name} import router as {var_name}_router\n"
        routers.append(f"{var_name}_router")
    
    init_content += "\n"
    init_content += "router = APIRouter(prefix=\"/internal\", tags=[\"internal\"])\n\n"
    
    # 包含所有 router（每个只包含一次）
    for router_var in routers:
        init_content += f"router.include_router({router_var})\n"
    
    init_path = INTERNAL_DIR / "__init__.py"
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(init_content)
    
    print(f"✓ 创建文件: {init_path}")


def backup_original_file():
    """备份原文件"""
    backup_path = INTERNAL_FILE.with_suffix('.py.backup')
    if INTERNAL_FILE.exists():
        import shutil
        shutil.copy2(INTERNAL_FILE, backup_path)
        print(f"✓ 备份原文件: {backup_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("拆分 internal.py 文件")
    print("=" * 60)
    
    # 检查文件是否存在
    if not INTERNAL_FILE.exists():
        print(f"❌ 文件不存在: {INTERNAL_FILE}")
        return
    
    # 创建 internal 目录
    INTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ 创建目录: {INTERNAL_DIR}")
    
    # 读取原文件
    print(f"📖 读取文件: {INTERNAL_FILE}")
    content = read_file_content(INTERNAL_FILE)
    
    # 找到模块边界
    print("🔍 分析模块...")
    boundaries = find_module_boundaries(content)
    
    # 按文件分组模块
    file_modules: Dict[str, List[Tuple[str, str]]] = {}  # file_name -> [(module_name, content)]
    
    for module_name, (start_line, end_line) in boundaries.items():
        module_def = MODULES[module_name]
        file_name = module_def["file"]
        
        if file_name not in file_modules:
            file_modules[file_name] = []
        
        module_content = extract_module_content(content, start_line, end_line)
        file_modules[file_name].append((module_name, module_content))
    
    # 写入每个文件
    print("\n📝 生成模块文件...")
    for file_name, modules in file_modules.items():
        file_path = INTERNAL_DIR / file_name
        
        # 合并多个模块的内容
        combined_content = "\n\n".join([content for _, content in modules])
        
        # 判断是否是 helpers.py
        is_helpers = file_name == "helpers.py"
        
        write_module_file(file_path, combined_content, file_name, is_helpers)
    
    # 创建 __init__.py
    print("\n📝 创建 __init__.py...")
    module_files = {name: MODULES[name]["file"] for name in boundaries.keys()}
    create_init_file(module_files)
    
    # 备份原文件
    print("\n💾 备份原文件...")
    backup_original_file()
    
    print("\n" + "=" * 60)
    print("✅ 拆分完成！")
    print("=" * 60)
    print(f"\n📁 新文件位置: {INTERNAL_DIR}")
    print(f"💾 原文件备份: {INTERNAL_FILE}.backup")
    print("\n⚠️  下一步:")
    print("   1. 检查生成的文件")
    print("   2. 运行测试确保功能正常")
    print("   3. 如果一切正常，可以删除备份文件")


if __name__ == "__main__":
    main()
