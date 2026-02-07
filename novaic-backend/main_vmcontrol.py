#!/usr/bin/env python3
"""
vmcontrol 服务启动脚本
独立运行的 Rust VM 控制服务
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vmcontrol')

def find_vmcontrol_binary():
    """查找 vmcontrol 二进制文件"""
    # 可能的位置
    project_root = Path(__file__).parent.parent
    possible_paths = [
        project_root / 'novaic-app/src-tauri/target/release/vmcontrol',
        project_root / 'novaic-app/src-tauri/target/debug/vmcontrol',
        project_root / 'novaic-app/src-tauri/vmcontrol/target/release/vmcontrol',
        project_root / 'novaic-app/src-tauri/vmcontrol/target/debug/vmcontrol',
        Path('/usr/local/bin/vmcontrol'),
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found vmcontrol at: {path}")
            return str(path)
    
    # 尝试从 PATH 查找
    import shutil
    if shutil.which('vmcontrol'):
        return 'vmcontrol'
    
    return None

def run_vmcontrol(args):
    """运行 vmcontrol 服务"""
    binary = args.binary or find_vmcontrol_binary()
    
    if not binary:
        logger.error("vmcontrol binary not found. Please build it first:")
        logger.error("  cd novaic-app/src-tauri/vmcontrol && cargo build --release")
        sys.exit(1)
    
    # 构建命令
    cmd = [binary]
    
    # 添加参数
    if args.port:
        cmd.extend(['--port', str(args.port)])
    if args.host:
        cmd.extend(['--host', args.host])
    
    # 设置环境变量
    env = os.environ.copy()
    env['RUST_LOG'] = args.log_level
    
    # 启动进程
    logger.info(f"Starting vmcontrol: {' '.join(cmd)}")
    logger.info(f"Port: {args.port}, Host: {args.host}")
    logger.info(f"Log level: {args.log_level}")
    
    try:
        process = subprocess.run(cmd, env=env)
        sys.exit(process.returncode)
    except KeyboardInterrupt:
        logger.info("Shutting down vmcontrol...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start vmcontrol: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='vmcontrol Service')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--binary', help='Path to vmcontrol binary')
    parser.add_argument('--log-level', default='info', help='Log level (trace, debug, info, warn, error)')
    
    args = parser.parse_args()
    run_vmcontrol(args)

if __name__ == '__main__':
    main()
