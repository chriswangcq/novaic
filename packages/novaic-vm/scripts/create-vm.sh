#!/bin/bash

# NovAIC VM - 创建虚拟机
# 下载 Ubuntu Cloud Image 并配置 cloud-init

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_DIR="$(dirname "$SCRIPT_DIR")"
IMAGES_DIR="$VM_DIR/images"
ISO_DIR="$VM_DIR/iso"
CONFIG_DIR="$VM_DIR/config"
FIRMWARE_DIR="$VM_DIR/firmware"

# Ubuntu 版本配置
UBUNTU_VERSION="24.04"
UBUNTU_CODENAME="noble"

# 镜像下载地址 (可自定义)
UBUNTU_MIRROR="${UBUNTU_MIRROR:-https://cloud-images.ubuntu.com}"

# VM 配置
VM_DISK_SIZE="${VM_DISK_SIZE:-40G}"
VM_NAME="novaic-vm"

# 镜像源配置：USE_CN_MIRRORS=1 使用中国镜像源
USE_CN_MIRRORS="${USE_CN_MIRRORS:-0}"

# ============================================================
# SSH 公钥检测与生成函数
# ============================================================
get_or_create_ssh_key() {
    local SSH_DIR="$HOME/.ssh"
    local SSH_PUBKEY=""
    
    # 按优先级检查现有公钥
    for key_type in id_ed25519 id_rsa id_ecdsa id_dsa; do
        if [ -f "$SSH_DIR/${key_type}.pub" ]; then
            SSH_PUBKEY=$(cat "$SSH_DIR/${key_type}.pub")
            echo "  ✓ 使用现有 SSH 公钥: ${key_type}.pub" >&2
            echo "$SSH_PUBKEY"
            return 0
        fi
    done
    
    # 没有现有公钥，自动生成 ed25519 密钥
    echo "  ⚠️  未找到 SSH 公钥，自动生成..." >&2
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    
    ssh-keygen -t ed25519 -f "$SSH_DIR/id_ed25519" -N "" -C "novaic-vm-$(date +%Y%m%d)" >/dev/null 2>&1
    
    if [ -f "$SSH_DIR/id_ed25519.pub" ]; then
        SSH_PUBKEY=$(cat "$SSH_DIR/id_ed25519.pub")
        echo "  ✓ 已生成新 SSH 密钥: id_ed25519" >&2
        echo "$SSH_PUBKEY"
        return 0
    else
        echo "  ❌ 生成 SSH 密钥失败" >&2
        return 1
    fi
}

echo ""
echo "════════════════════════════════════════════"
echo "  NovAIC VM - 创建 Ubuntu $UBUNTU_VERSION 虚拟机"
echo "════════════════════════════════════════════"
echo ""

# 检测架构
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    UBUNTU_ARCH="arm64"
    CLOUD_IMAGE="${UBUNTU_CODENAME}-server-cloudimg-arm64.img"
    echo "架构: Apple Silicon (arm64)"
else
    UBUNTU_ARCH="amd64"
    CLOUD_IMAGE="${UBUNTU_CODENAME}-server-cloudimg-amd64.img"
    echo "架构: Intel (x86_64)"
fi

# 显示镜像源配置
if [ "$USE_CN_MIRRORS" = "1" ]; then
    echo "镜像源: 中国 (阿里云)"
    if [ "$ARCH" = "arm64" ]; then
        APT_MIRROR="mirrors.aliyun.com/ubuntu-ports"
    else
        APT_MIRROR="mirrors.aliyun.com/ubuntu"
    fi
    PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
    PIP_TRUSTED_HOST="mirrors.aliyun.com"
else
    echo "镜像源: 官方 (全球)"
    if [ "$ARCH" = "arm64" ]; then
        APT_MIRROR="ports.ubuntu.com/ubuntu-ports"
    else
        APT_MIRROR="archive.ubuntu.com/ubuntu"
    fi
    PIP_INDEX_URL="https://pypi.org/simple/"
    PIP_TRUSTED_HOST="pypi.org"
fi
echo ""

# 创建目录
mkdir -p "$IMAGES_DIR" "$ISO_DIR" "$CONFIG_DIR" "$FIRMWARE_DIR"

# ============================================================
# Step 1: 下载 Ubuntu Cloud Image
# ============================================================
echo "[1/4] 下载 Ubuntu Cloud Image..."

DOWNLOAD_URL="${UBUNTU_MIRROR}/${UBUNTU_CODENAME}/current/${CLOUD_IMAGE}"

if [ -f "$ISO_DIR/$CLOUD_IMAGE" ]; then
    echo "  ✓ 已存在: $CLOUD_IMAGE"
else
    echo "  下载: $DOWNLOAD_URL"
    curl -L --progress-bar -o "$ISO_DIR/$CLOUD_IMAGE" "$DOWNLOAD_URL"
    echo "  ✓ 下载完成"
fi

# ============================================================
# Step 2: 创建 VM 磁盘
# ============================================================
echo ""
echo "[2/4] 创建 VM 磁盘..."

VM_DISK="$IMAGES_DIR/${VM_NAME}.qcow2"

if [ -f "$VM_DISK" ]; then
    rm -f "$VM_DISK"
fi

qemu-img convert -f qcow2 -O qcow2 "$ISO_DIR/$CLOUD_IMAGE" "$VM_DISK"
qemu-img resize "$VM_DISK" "$VM_DISK_SIZE"
echo "  ✓ 磁盘创建完成: ${VM_NAME}.qcow2 ($VM_DISK_SIZE)"

# ============================================================
# Step 3: 创建 UEFI 固件 (ARM64)
# ============================================================
if [ "$ARCH" = "arm64" ]; then
    echo ""
    echo "[2.5/4] 配置 UEFI 固件..."
    
    # 下载 UEFI 固件 (如果不存在)
    if [ ! -f "$FIRMWARE_DIR/QEMU_EFI.fd" ]; then
        echo "  下载 UEFI 固件..."
        # 从 Homebrew 复制
        BREW_QEMU_SHARE="$(brew --prefix)/share/qemu"
        if [ -f "$BREW_QEMU_SHARE/edk2-aarch64-code.fd" ]; then
            cp "$BREW_QEMU_SHARE/edk2-aarch64-code.fd" "$FIRMWARE_DIR/QEMU_EFI.fd"
        else
            echo "  ⚠️ 未找到 UEFI 固件，尝试从网络下载..."
            curl -L -o "$FIRMWARE_DIR/QEMU_EFI.fd" \
                "https://releases.linaro.org/components/kernel/uefi-linaro/latest/release/qemu64/QEMU_EFI.fd"
        fi
    fi
    
    # 创建 UEFI 变量文件
    if [ ! -f "$FIRMWARE_DIR/QEMU_VARS.fd" ]; then
        dd if=/dev/zero of="$FIRMWARE_DIR/QEMU_VARS.fd" bs=1M count=64 2>/dev/null
    fi
    
    echo "  ✓ UEFI 固件已配置"
fi

# ============================================================
# Step 4: 检测/生成 SSH 公钥
# ============================================================
echo ""
echo "[3/5] 配置 SSH 公钥..."

SSH_KEY_DIR="$HOME/.ssh"
SSH_PUB_KEY=""
SSH_KEY_SOURCE=""

# 检测已有的 SSH 公钥（按优先级顺序）
for key_file in "$SSH_KEY_DIR/id_ed25519.pub" "$SSH_KEY_DIR/id_rsa.pub" "$SSH_KEY_DIR/id_ecdsa.pub"; do
    if [ -f "$key_file" ]; then
        SSH_PUB_KEY=$(cat "$key_file")
        SSH_KEY_SOURCE="$key_file"
        break
    fi
done

# 如果没有找到公钥，自动生成一个
if [ -z "$SSH_PUB_KEY" ]; then
    echo "  ⚠️ 未检测到 SSH 公钥，自动生成..."
    
    # 确保 .ssh 目录存在
    mkdir -p "$SSH_KEY_DIR"
    chmod 700 "$SSH_KEY_DIR"
    
    # 生成 ed25519 密钥（更现代、更安全）
    SSH_KEY_FILE="$SSH_KEY_DIR/id_ed25519_novaic"
    if [ ! -f "$SSH_KEY_FILE" ]; then
        ssh-keygen -t ed25519 -f "$SSH_KEY_FILE" -N "" -C "novaic-vm-$(date +%Y%m%d)"
        echo "  ✓ 已生成新的 SSH 密钥对: $SSH_KEY_FILE"
    else
        echo "  ✓ 使用已有的 NovAIC SSH 密钥: $SSH_KEY_FILE"
    fi
    
    SSH_PUB_KEY=$(cat "${SSH_KEY_FILE}.pub")
    SSH_KEY_SOURCE="${SSH_KEY_FILE}.pub"
else
    echo "  ✓ 检测到已有 SSH 公钥: $SSH_KEY_SOURCE"
fi

echo "  ✓ SSH 公钥将被配置到 VM"

# ============================================================
# Step 5: 创建 cloud-init 配置
# ============================================================
echo ""
echo "[4/5] 创建 cloud-init 配置..."

# meta-data
cat > "$CONFIG_DIR/meta-data" << EOF
instance-id: ${VM_NAME}
local-hostname: ${VM_NAME}
EOF

# user-data (从模板复制或使用默认)
# 生成 user-data 配置（动态插入 SSH 公钥）
cat > "$CONFIG_DIR/user-data" << EOF
#cloud-config

# =====================================================
# NovAIC VM - Ubuntu Cloud-Init Configuration
# =====================================================

# 用户配置
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    groups: [adm, audio, cdrom, dialout, dip, floppy, lxd, netdev, plugdev, sudo, video]
    ssh_authorized_keys:
      - ${SSH_PUB_KEY}

# 设置密码
chpasswd:
  list: |
    ubuntu:ubuntu
  expire: false

# SSH 配置
ssh_pwauth: true

# APT 源配置
apt:
  primary:
    - arches: [default]
      uri: http://${APT_MIRROR}
  sources_list: |
    deb http://${APT_MIRROR} ${UBUNTU_CODENAME} main restricted universe multiverse
    deb http://${APT_MIRROR} ${UBUNTU_CODENAME}-updates main restricted universe multiverse
    deb http://${APT_MIRROR} ${UBUNTU_CODENAME}-backports main restricted universe multiverse
    deb http://${APT_MIRROR} ${UBUNTU_CODENAME}-security main restricted universe multiverse
EOF

# 追加其余配置（使用单引号防止变量展开）
cat >> "$CONFIG_DIR/user-data" << 'USERDATA_EOF'

# 包更新
package_update: true
package_upgrade: false

# 安装软件包
packages:
  # 桌面环境 (XFCE - 轻量级)
  - xfce4
  - xfce4-terminal
  - xfce4-goodies
  - lightdm
  - lightdm-gtk-greeter
  - dbus-x11
  
  # VNC 服务
  - x11vnc
  - xvfb
  
  # 浏览器
  - chromium-browser
  
  # 桌面自动化工具
  - xdotool
  - wmctrl
  - scrot
  - imagemagick
  
  # Python
  - python3
  - python3-pip
  - python3-venv
  
  # 网络工具
  - curl
  - wget
  - net-tools
  - openssh-server
  
  # 其他
  - git
  - vim
  - htop

# 写入配置文件
write_files:
  # LightDM 自动登录
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      user-session=xfce

  # x11vnc 服务
  - path: /etc/systemd/system/x11vnc.service
    content: |
      [Unit]
      Description=x11vnc VNC Server
      After=display-manager.service
      Requires=display-manager.service

      [Service]
      Type=simple
      User=ubuntu
      Environment=DISPLAY=:0
      ExecStartPre=/bin/sleep 5
      ExecStart=/usr/bin/x11vnc -display :0 -auth guess -forever -loop -noxdamage -repeat -rfbport 5900 -shared -rfbauth /home/ubuntu/.vnc/passwd
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

  # VNC 密码设置脚本 (密码: 1)
  - path: /home/ubuntu/setup-vnc.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      mkdir -p /home/ubuntu/.vnc
      x11vnc -storepasswd 1 /home/ubuntu/.vnc/passwd
      chmod 600 /home/ubuntu/.vnc/passwd

  # NovAIC 服务 (预留，部署时启用)
  - path: /etc/systemd/system/novaic.service
    content: |
      [Unit]
      Description=NovAIC Core - MCP Server
      After=network.target display-manager.service x11vnc.service
      Wants=display-manager.service

      [Service]
      Type=simple
      User=ubuntu
      Environment=DISPLAY=:0
      Environment=XAUTHORITY=/home/ubuntu/.Xauthority
      Environment=HOME=/home/ubuntu
      Environment=PATH=/opt/novaic-venv/bin:/usr/local/bin:/usr/bin:/bin
      Environment=NOVAIC_HOST=0.0.0.0
      Environment=NOVAIC_PORT=8081
      WorkingDirectory=/opt/novaic-core
      ExecStart=/opt/novaic-venv/bin/python -m uvicorn novaic_core.main:app --host 0.0.0.0 --port 8081
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

  # 禁用屏幕保护
  - path: /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml
    content: |
      <?xml version="1.0" encoding="UTF-8"?>
      <channel name="xfce4-power-manager" version="1.0">
        <property name="xfce4-power-manager" type="empty">
          <property name="dpms-enabled" type="bool" value="false"/>
          <property name="blank-on-ac" type="int" value="0"/>
          <property name="dpms-on-ac-sleep" type="uint" value="0"/>
          <property name="dpms-on-ac-off" type="uint" value="0"/>
        </property>
      </channel>

# 启动命令
runcmd:
  # 修复 /home/ubuntu 目录权限 (重要!)
  - chown -R ubuntu:ubuntu /home/ubuntu
  
  # 设置 VNC 密码
  - su - ubuntu -c '/home/ubuntu/setup-vnc.sh'
  
  # 创建 xfce4 配置目录
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - chown -R ubuntu:ubuntu /home/ubuntu/.config
  
  # 等待网络就绪
  - echo "Waiting for network..."
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  
  # 创建 novaic 目录
  - mkdir -p /opt/novaic-core /opt/novaic-venv
  - chown -R ubuntu:ubuntu /opt/novaic-core /opt/novaic-venv
  
  # 启用服务
  - systemctl daemon-reload
  - systemctl enable lightdm
  - systemctl enable x11vnc
  - systemctl start lightdm
  
  # 等待桌面启动后启动 VNC
  - sleep 10
  - systemctl start x11vnc
  
  # 完成标记
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log

final_message: |
  =====================================================
  NovAIC VM 配置完成!
  =====================================================
  
  VNC: vnc://localhost:5900 (密码: 1)
  SSH: ssh -p 2222 ubuntu@localhost (密码: ubuntu)
  
  请运行 deploy.sh 部署 MCP Server
USERDATA_EOF

# 创建 cloud-init ISO
echo "  创建 cloud-init ISO..."
SEED_ISO="$ISO_DIR/cloud-init-seed.iso"

if command -v mkisofs &> /dev/null; then
    mkisofs -output "$SEED_ISO" -volid cidata -joliet -rock \
        "$CONFIG_DIR/user-data" "$CONFIG_DIR/meta-data" 2>/dev/null
elif command -v genisoimage &> /dev/null; then
    genisoimage -output "$SEED_ISO" -volid cidata -joliet -rock \
        "$CONFIG_DIR/user-data" "$CONFIG_DIR/meta-data" 2>/dev/null
elif command -v hdiutil &> /dev/null; then
    TEMP_DIR=$(mktemp -d)
    cp "$CONFIG_DIR/user-data" "$TEMP_DIR/"
    cp "$CONFIG_DIR/meta-data" "$TEMP_DIR/"
    hdiutil makehybrid -o "${SEED_ISO%.iso}" -hfs -joliet -iso -default-volume-name cidata "$TEMP_DIR" 2>/dev/null
    rm -rf "$TEMP_DIR"
else
    echo "  ❌ 错误: 需要 mkisofs, genisoimage 或 hdiutil"
    exit 1
fi

echo "  ✓ cloud-init ISO 创建完成"

# ============================================================
# 完成
# ============================================================
echo ""
echo "[4/4] 完成!"
echo ""
echo "════════════════════════════════════════════"
echo "  VM 创建成功!"
echo "════════════════════════════════════════════"
echo ""
echo "磁盘: $IMAGES_DIR/${VM_NAME}.qcow2"
echo "大小: $VM_DISK_SIZE"
echo ""
echo "启动 VM: ./scripts/start-vm.sh"
echo ""
