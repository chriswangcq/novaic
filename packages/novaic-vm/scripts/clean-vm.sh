#!/bin/bash

# NovAIC VM - 清理虚拟机（保留已下载的镜像）
# 用法: ./scripts/clean-vm.sh [--all]
#   默认: 保留已下载的 Ubuntu Cloud Image
#   --all: 删除所有文件，包括下载的镜像

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 清理虚拟机"
echo "════════════════════════════════════════════"
echo ""

# 先停止 VM
if [ -f "$VM_DIR/.vm.pid" ]; then
    PID=$(cat "$VM_DIR/.vm.pid")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "停止运行中的 VM (PID: $PID)..."
        kill -TERM "$PID" 2>/dev/null || true
        sleep 2
        kill -9 "$PID" 2>/dev/null || true
    fi
    rm -f "$VM_DIR/.vm.pid"
fi

# 检查参数
if [ "$1" = "--all" ]; then
    echo "模式: 完全清理 (包括下载的镜像)"
    echo ""
    
    rm -rf "$VM_DIR/images" "$VM_DIR/config" "$VM_DIR/firmware" "$VM_DIR/iso"
    
    echo "已删除:"
    echo "  ✓ images/     (VM 磁盘)"
    echo "  ✓ config/     (cloud-init 配置)"
    echo "  ✓ firmware/   (UEFI 固件)"
    echo "  ✓ iso/        (Ubuntu 镜像 + cloud-init ISO)"
else
    echo "模式: 快速清理 (保留已下载的镜像)"
    echo ""
    
    # 删除 VM 磁盘
    rm -rf "$VM_DIR/images"
    echo "  ✓ images/     (VM 磁盘)"
    
    # 删除 cloud-init 配置
    rm -rf "$VM_DIR/config"
    echo "  ✓ config/     (cloud-init 配置)"
    
    # 删除 UEFI 变量文件（保留固件）
    rm -f "$VM_DIR/firmware/QEMU_VARS.fd"
    echo "  ✓ firmware/QEMU_VARS.fd"
    
    # 删除 cloud-init ISO（保留 Ubuntu 镜像）
    rm -f "$VM_DIR/iso/cloud-init-seed.iso"
    echo "  ✓ iso/cloud-init-seed.iso"
    
    # 显示保留的文件
    echo ""
    echo "已保留:"
    if [ -f "$VM_DIR/firmware/QEMU_EFI.fd" ]; then
        echo "  ✓ firmware/QEMU_EFI.fd (UEFI 固件)"
    fi
    if ls "$VM_DIR/iso/"*.img 1> /dev/null 2>&1; then
        for img in "$VM_DIR/iso/"*.img; do
            size=$(du -h "$img" | cut -f1)
            echo "  ✓ iso/$(basename "$img") ($size)"
        done
    fi
fi

echo ""
echo "════════════════════════════════════════════"
echo "  清理完成"
echo "════════════════════════════════════════════"
echo ""
echo "重建 VM: ./scripts/create-vm.sh"
echo ""
