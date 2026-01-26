#!/bin/bash

# NovAIC VM - 重置并部署虚拟机
# 
# 用法:
#   ./scripts/reset-vm.sh              # 使用官方源（全球）
#   USE_CN_MIRRORS=1 ./scripts/reset-vm.sh  # 使用中国镜像源（阿里云）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# 显示配置
echo ""
if [ "${USE_CN_MIRRORS:-0}" = "1" ]; then
    echo "镜像源模式: 中国 (阿里云)"
else
    echo "镜像源模式: 官方 (全球)"
fi
echo ""

# 1. 停止 VM
./scripts/stop-vm.sh

# 2. 清理 VM（保留已下载的镜像）
./scripts/clean-vm.sh

# 3. 重新创建 VM（apt 源在此配置）
./scripts/create-vm.sh

# 4. 启动 VM
./scripts/start-vm.sh

# 5. 部署（会自动等待 cloud-init 完成）
./scripts/deploy.sh
