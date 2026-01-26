#!/bin/bash

# NovAIC VM - 启动虚拟机

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
IMAGES_DIR="$VM_DIR/images"
ISO_DIR="$VM_DIR/iso"
FIRMWARE_DIR="$VM_DIR/firmware"

VM_DISK="$IMAGES_DIR/novaic-vm.qcow2"
SEED_ISO="$ISO_DIR/cloud-init-seed.iso"
PID_FILE="$VM_DIR/.vm.pid"

# VM 配置
MEMORY="${NOVAIC_VM_MEMORY:-4096}"
CPUS="${NOVAIC_VM_CPUS:-4}"

# 端口配置 (宿主机端口)
VNC_PORT="${NOVAIC_VNC_PORT:-5900}"
MCP_PORT="${NOVAIC_MCP_PORT:-8081}"
SSH_PORT="${NOVAIC_SSH_PORT:-2222}"
WEBSOCKET_PORT="${NOVAIC_WS_PORT:-6080}"

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 启动虚拟机"
echo "════════════════════════════════════════════"
echo ""

# 检查 VM 磁盘
if [ ! -f "$VM_DISK" ]; then
    echo "❌ 错误: VM 磁盘不存在"
    echo "请先运行: ./scripts/create-vm.sh"
    exit 1
fi

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  VM 已在运行 (PID: $OLD_PID)"
        echo ""
        echo "停止 VM: ./scripts/stop-vm.sh"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# 检测架构并配置 QEMU
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    QEMU_CMD="qemu-system-aarch64"
    MACHINE="-M virt,highmem=on -cpu host"
    ACCEL="-accel hvf"
    
    # UEFI 固件
    UEFI_FW="$FIRMWARE_DIR/QEMU_EFI.fd"
    UEFI_VARS="$FIRMWARE_DIR/QEMU_VARS.fd"
    
    if [ ! -f "$UEFI_FW" ]; then
        echo "❌ 错误: UEFI 固件不存在"
        echo "请先运行: ./scripts/create-vm.sh"
        exit 1
    fi
    
    DRIVE_OPTS="-drive if=pflash,format=raw,file=$UEFI_FW,readonly=on"
    DRIVE_OPTS="$DRIVE_OPTS -drive if=pflash,format=raw,file=$UEFI_VARS"
    DRIVE_OPTS="$DRIVE_OPTS -drive if=none,id=hd0,format=qcow2,file=$VM_DISK"
    DRIVE_OPTS="$DRIVE_OPTS -device virtio-blk-pci,drive=hd0,bootindex=1"
    
    # Cloud-init ISO
    CDROM_OPTS="-device virtio-scsi-pci,id=scsi0"
    CDROM_OPTS="$CDROM_OPTS -drive if=none,id=cd0,format=raw,file=$SEED_ISO,readonly=on"
    CDROM_OPTS="$CDROM_OPTS -device scsi-cd,drive=cd0,bus=scsi0.0"
    
    DISPLAY_DEV="-device virtio-gpu-pci"
    
    echo "架构: Apple Silicon (arm64)"
else
    QEMU_CMD="qemu-system-x86_64"
    MACHINE="-M q35 -cpu host"
    ACCEL="-accel hvf"
    DRIVE_OPTS="-hda $VM_DISK"
    CDROM_OPTS="-cdrom $SEED_ISO"
    DISPLAY_DEV=""
    
    echo "架构: Intel (x86_64)"
fi

# 网络端口转发 (主机端口 → VM端口，统一使用相同端口号)
NET_FWD="hostfwd=tcp::${VNC_PORT}-:5900"
NET_FWD="$NET_FWD,hostfwd=tcp::${MCP_PORT}-:8081"
NET_FWD="$NET_FWD,hostfwd=tcp::${SSH_PORT}-:22"
NET_FWD="$NET_FWD,hostfwd=tcp::${WEBSOCKET_PORT}-:6080"

echo ""
echo "配置:"
echo "  内存: ${MEMORY}MB"
echo "  CPU:  ${CPUS} 核心"
echo ""
echo "端口映射:"
echo "  VNC:       localhost:$VNC_PORT → VM:5900"
echo "  MCP:       localhost:$MCP_PORT → VM:8081"
echo "  SSH:       localhost:$SSH_PORT → VM:22"
echo "  WebSocket: localhost:$WEBSOCKET_PORT → VM:6080"
echo ""

# 启动模式
MODE="${1:---foreground}"

if [ "$MODE" == "-d" ] || [ "$MODE" == "--daemon" ]; then
    echo "启动模式: 后台运行"
    echo ""
    
    $QEMU_CMD \
        $MACHINE \
        $ACCEL \
        -m "$MEMORY" \
        -smp "$CPUS" \
        $DRIVE_OPTS \
        $CDROM_OPTS \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,$NET_FWD \
        $DISPLAY_DEV \
        -device usb-ehci \
        -device usb-kbd \
        -device usb-mouse \
        -display none \
        -daemonize \
        -pidfile "$PID_FILE"
else
    echo "启动模式: 前台运行 (带 QEMU 窗口)"
    echo ""
    
    $QEMU_CMD \
        $MACHINE \
        $ACCEL \
        -m "$MEMORY" \
        -smp "$CPUS" \
        $DRIVE_OPTS \
        $CDROM_OPTS \
        -device virtio-net-pci,netdev=net0 \
        -netdev user,id=net0,$NET_FWD \
        $DISPLAY_DEV \
        -device usb-ehci \
        -device usb-kbd \
        -device usb-mouse \
        -display cocoa &
    
    echo $! > "$PID_FILE"
fi

sleep 2

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ VM 已启动 (PID: $PID)"
    else
        echo "❌ VM 启动失败"
        rm -f "$PID_FILE"
        exit 1
    fi
fi

echo ""
echo "════════════════════════════════════════════"
echo ""
echo "首次启动需要 5-10 分钟完成系统配置..."
echo ""
echo "检查进度:"
echo "  ssh -p $SSH_PORT ubuntu@localhost"
echo "  tail -f /var/log/cloud-init-output.log"
echo ""
echo "连接方式:"
echo "  VNC: vnc://localhost:$VNC_PORT (密码: novaic)"
echo "  SSH: ssh -p $SSH_PORT ubuntu@localhost (密码: ubuntu)"
echo "  MCP: http://localhost:$MCP_PORT/sse (部署后可用)"
echo ""
echo "管理命令:"
echo "  停止:   ./scripts/stop-vm.sh"
echo "  状态:   ./scripts/status-vm.sh"
echo "  部署:   ./scripts/deploy.sh"
echo ""
