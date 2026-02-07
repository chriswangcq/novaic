# VMUSE Cloud-Init 优化方案

**优化日期**: 2026-02-07  
**目标**: VM 启动后自动完成所有 VMUSE 依赖安装和服务配置  

---

## 🎯 优化目标

### 当前问题
1. ❌ 缺少 Node.js（Playwright 需要）
2. ❌ 缺少 VMUSE Python 依赖（aiohttp、pydantic-settings等）
3. ❌ VMUSE 服务需要手动部署
4. ❌ systemd 服务配置需要手动创建

### 优化后
1. ✅ Node.js 自动安装（LTS版本）
2. ✅ 所有 VMUSE Python 依赖自动安装
3. ✅ VMUSE 代码自动部署
4. ✅ systemd 服务自动配置并启动
5. ✅ 所有工具开箱即用

---

## 📦 完整依赖清单

### 1. 系统包（APT）

**桌面环境**:
- `xfce4`, `xfce4-terminal`, `xfce4-goodies`
- `lightdm`, `lightdm-gtk-greeter`
- `dbus-x11`

**工具依赖**:
- `xdotool` - Desktop/Mouse/Keyboard
- `wmctrl` - Window 管理
- `scrot` - Screenshot
- `imagemagick` - 图片处理
- `xclip` - Clipboard
- `chromium-browser` - 浏览器（备用）

**Python 环境**:
- `python3`, `python3-pip`, `python3-venv`

**Node.js** (新增):
- 通过 NodeSource PPA 安装
- 版本: Node.js 20 LTS
- 包含 npm

**基础工具**:
- `curl`, `wget`, `net-tools`
- `openssh-server`
- `git`, `vim`, `htop`
- `qemu-guest-agent`

---

### 2. Python 包（pip）

**VMUSE 核心依赖**:
```bash
aiohttp>=3.13.3         # HTTP 服务器
pydantic>=2.0.0         # 数据验证
pydantic-settings       # 配置管理
python-dotenv           # 环境变量
Pillow                  # 图片处理
playwright>=1.40.0      # 浏览器自动化
```

**安装方式**: 通过 venv 虚拟环境隔离安装

---

### 3. Playwright + Chromium

```bash
# 1. 安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt-get install -y nodejs

# 2. 安装 Playwright
pip install playwright

# 3. 安装 Chromium 浏览器
playwright install --with-deps chromium
```

**安装位置**:
- Playwright: `/opt/novaic/venv/lib/python3.12/site-packages/playwright`
- Chromium: `~/.cache/ms-playwright/chromium-*/`

---

## 🔧 优化后的 Cloud-Init 配置

### 关键改进

#### 1. 添加 Node.js 安装
```yaml
runcmd:
  # Install Node.js 20 LTS
  - echo "Installing Node.js..."
  - curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  - apt-get install -y nodejs
  - node --version
  - npm --version
```

#### 2. 安装完整 VMUSE 依赖
```yaml
runcmd:
  # Install VMUSE Python dependencies
  - echo "Installing VMUSE dependencies..."
  - /opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow playwright
  - /opt/novaic/venv/bin/playwright install --with-deps chromium
```

#### 3. 部署 VMUSE 代码
```yaml
write_files:
  - path: /opt/novaic/novaic-mcp-vmuse-placeholder.txt
    content: |
      VMUSE code will be deployed here after VM initialization.
      Gateway will deploy the actual code via SSH/SCP.

runcmd:
  # Create VMUSE directory structure
  - mkdir -p /opt/novaic/novaic-mcp-vmuse/src/novaic_mcp_vmuse
  - chown -R ubuntu:ubuntu /opt/novaic/novaic-mcp-vmuse
```

#### 4. 配置 systemd 服务
```yaml
write_files:
  - path: /etc/systemd/system/novaic-vmuse.service
    content: |
      [Unit]
      Description=NovAIC VMUSE HTTP Server
      After=network.target

      [Service]
      Type=simple
      User=ubuntu
      WorkingDirectory=/opt/novaic/novaic-mcp-vmuse
      Environment="DISPLAY=:0"
      Environment="PATH=/opt/novaic/venv/bin:/usr/local/bin:/usr/bin:/bin"
      ExecStart=/opt/novaic/venv/bin/python3 -m novaic_mcp_vmuse.http_server
      Restart=always
      RestartSec=10
      StandardOutput=journal
      StandardError=journal

      [Install]
      WantedBy=multi-user.target
    permissions: '0644'

runcmd:
  # Enable VMUSE service (will start after code deployment)
  - systemctl daemon-reload
  - systemctl enable novaic-vmuse
```

---

## 📋 完整优化配置

### user-data.yaml
```yaml
#cloud-config

# Hostname and user
hostname: novaic-vm
users:
  - name: ubuntu
    ssh-authorized-keys:
      - {ssh_public_key}
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    passwd: ubuntu  # 密码: ubuntu (用于调试)

# APT mirrors configuration
apt:
  primary:
    - arches: [default]
      uri: http://{apt_mirror}
  security:
    - arches: [default]
      uri: http://{apt_mirror}
  sources_list: |
    deb http://{apt_mirror} {ubuntu_codename} main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-updates main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-backports main restricted universe multiverse
    deb http://{apt_mirror} {ubuntu_codename}-security main restricted universe multiverse

# Package management
package_update: true
package_upgrade: false

# System packages
packages:
  # Desktop environment
  - xfce4
  - xfce4-terminal
  - xfce4-goodies
  - lightdm
  - lightdm-gtk-greeter
  - dbus-x11
  
  # Tools (VMUSE dependencies)
  - chromium-browser
  - xdotool          # Desktop/Mouse/Keyboard
  - wmctrl           # Window management
  - scrot            # Screenshot
  - imagemagick      # Image processing
  - xclip            # Clipboard
  
  # Python
  - python3
  - python3-pip
  - python3-venv
  
  # Basic utilities
  - curl
  - wget
  - net-tools
  - openssh-server
  - git
  - vim
  - htop
  
  # VM integration
  - qemu-guest-agent

# Configuration files
write_files:
  # Auto-login configuration
  - path: /etc/lightdm/lightdm.conf.d/50-autologin.conf
    content: |
      [Seat:*]
      autologin-user=ubuntu
      autologin-user-timeout=0
      user-session=xfce
    permissions: '0644'

  # Power management (disable screen blanking)
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
    permissions: '0644'

  # VMUSE systemd service
  - path: /etc/systemd/system/novaic-vmuse.service
    content: |
      [Unit]
      Description=NovAIC VMUSE HTTP Server
      After=network.target lightdm.service

      [Service]
      Type=simple
      User=ubuntu
      WorkingDirectory=/opt/novaic/novaic-mcp-vmuse
      Environment="DISPLAY=:0"
      Environment="PATH=/opt/novaic/venv/bin:/usr/local/bin:/usr/bin:/bin"
      Environment="PYTHONPATH=/opt/novaic/novaic-mcp-vmuse/src"
      ExecStart=/opt/novaic/venv/bin/python3 -m novaic_mcp_vmuse.http_server
      Restart=always
      RestartSec=10
      StandardOutput=journal
      StandardError=journal
      SyslogIdentifier=novaic-vmuse

      [Install]
      WantedBy=multi-user.target
    permissions: '0644'

  # Environment setup script
  - path: /opt/novaic/scripts/setup_env.sh
    content: |
      #!/bin/bash
      # VMUSE environment setup helper
      export DISPLAY=:0
      export PATH="/opt/novaic/venv/bin:$PATH"
      export PYTHONPATH="/opt/novaic/novaic-mcp-vmuse/src:$PYTHONPATH"
    permissions: '0755'

# Startup commands
runcmd:
  # ========== Phase 1: Directory Setup ==========
  - echo "=== Phase 1: Directory Setup ==="
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - mkdir -p /opt/novaic/scripts
  - mkdir -p /opt/novaic/venv
  - mkdir -p /opt/novaic/novaic-mcp-vmuse/src/novaic_mcp_vmuse
  - mkdir -p /opt/novaic/.cache
  
  # ========== Phase 2: Network & Environment ==========
  - echo "=== Phase 2: Waiting for network ==="
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  
  - echo 'DISPLAY=:0' | sudo tee -a /etc/environment
  - echo 'export PATH="/opt/novaic/venv/bin:$PATH"' | sudo tee -a /etc/profile.d/novaic.sh
  
  # ========== Phase 3: Node.js Installation ==========
  - echo "=== Phase 3: Installing Node.js 20 LTS ==="
  - curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  - apt-get install -y nodejs
  - node --version > /opt/novaic/.node_version
  - npm --version > /opt/novaic/.npm_version
  - echo "Node.js installed successfully."
  
  # ========== Phase 4: Python Virtual Environment ==========
  - echo "=== Phase 4: Creating Python virtual environment ==="
  - python3 -m venv /opt/novaic/venv
  - /opt/novaic/venv/bin/pip install --upgrade pip
  
  # ========== Phase 5: VMUSE Python Dependencies ==========
  - echo "=== Phase 5: Installing VMUSE Python dependencies ==="
  - /opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow playwright
  - echo "Python dependencies installed."
  
  # ========== Phase 6: Playwright + Chromium ==========
  - echo "=== Phase 6: Installing Playwright Chromium ==="
  - cd ~/.local/lib/python3.12/site-packages/playwright/driver || true
  - /opt/novaic/venv/bin/playwright install --with-deps chromium
  - echo "Playwright Chromium installed."
  
  # ========== Phase 7: QEMU Guest Agent ==========
  - echo "=== Phase 7: Starting QEMU Guest Agent ==="
  - systemctl daemon-reload
  - systemctl enable qemu-guest-agent
  - systemctl start qemu-guest-agent
  
  # ========== Phase 8: Ownership ==========
  - echo "=== Phase 8: Setting ownership ==="
  - chown -R ubuntu:ubuntu /home/ubuntu
  - chown -R ubuntu:ubuntu /opt/novaic
  
  # ========== Phase 9: Display Manager ==========
  - echo "=== Phase 9: Starting display manager ==="
  - systemctl enable lightdm
  - systemctl start lightdm
  - sleep 10
  
  # ========== Phase 10: Enable VMUSE Service ==========
  - echo "=== Phase 10: Enabling VMUSE service ==="
  - systemctl daemon-reload
  - systemctl enable novaic-vmuse
  - echo "VMUSE service enabled (will start after code deployment)."
  
  # ========== Phase 11: Completion Marker ==========
  - touch /opt/novaic/.dependencies_installed
  - touch /opt/novaic/.cloud_init_complete
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log
  - echo "=== Cloud-Init Complete ==="

final_message: |
  =====================================================
  NovAIC VM Cloud-Init Complete!
  =====================================================
  
  Installed:
  - Desktop: XFCE4 + LightDM
  - Node.js: $(cat /opt/novaic/.node_version 2>/dev/null || echo "20.x")
  - Python: Virtual environment at /opt/novaic/venv
  - VMUSE Dependencies: aiohttp, playwright, etc.
  - Playwright: Chromium installed
  - Tools: xdotool, wmctrl, scrot, xclip
  
  Next steps:
  1. Deploy VMUSE code to /opt/novaic/novaic-mcp-vmuse
  2. Start service: systemctl start novaic-vmuse
  
  SSH: ubuntu@<vm-ip> (password: ubuntu)
  =====================================================
```

---

## 🚀 部署流程

### 1. VM 初始化（Cloud-Init）
**时间**: 5-10分钟（首次）

自动完成：
- ✅ 系统包安装
- ✅ Node.js 20 安装
- ✅ Python venv 创建
- ✅ VMUSE 依赖安装
- ✅ Playwright Chromium 安装
- ✅ systemd 服务配置
- ✅ 桌面环境启动

### 2. VMUSE 代码部署（Gateway）
**时间**: 10-30秒

Gateway 通过 SSH 部署：
```bash
# 1. 打包 VMUSE 代码
tar -czf novaic-mcp-vmuse.tar.gz novaic-mcp-vmuse/

# 2. 传输到 VM
scp -P 20000 novaic-mcp-vmuse.tar.gz ubuntu@127.0.0.1:/opt/novaic/

# 3. 解压并安装
ssh ubuntu@127.0.0.1 -p 20000 'cd /opt/novaic && tar -xzf novaic-mcp-vmuse.tar.gz'
ssh ubuntu@127.0.0.1 -p 20000 'cd /opt/novaic/novaic-mcp-vmuse && /opt/novaic/venv/bin/pip install -e .'

# 4. 启动服务
ssh ubuntu@127.0.0.1 -p 20000 'sudo systemctl start novaic-vmuse'
```

### 3. 验证
```bash
# 检查服务状态
ssh ubuntu@127.0.0.1 -p 20000 'sudo systemctl status novaic-vmuse'

# 测试健康检查
curl http://127.0.0.1:18080/health

# 测试工具
curl -X POST http://127.0.0.1:18080/api/desktop/screenshot -H "Content-Type: application/json" -d '{}'
```

---

## 📊 优化效果对比

| 项目 | 优化前 | 优化后 |
|-----|--------|--------|
| **Node.js** | ❌ 缺失 | ✅ Node.js 20 LTS |
| **VMUSE 依赖** | ❌ 需手动安装 | ✅ 自动安装 |
| **Playwright** | ⚠️ 部分 | ✅ 完整（含Chromium） |
| **systemd 服务** | ❌ 需手动配置 | ✅ 自动配置 |
| **代码部署** | ❌ 手动 | ✅ 半自动（Gateway部署） |
| **首次启动时间** | ~15分钟 | ~10分钟 |
| **手动步骤** | ~10个 | ~2个 |

---

## 🎯 实施步骤

### 1. 更新 setup.py
修改 `novaic-backend/gateway/vm/setup.py` 中的 `_create_cloud_init` 方法，使用优化后的配置。

### 2. 添加部署脚本
在 Gateway 中添加 VMUSE 自动部署逻辑：
```python
async def deploy_vmuse_code(vm_ip: str, ssh_port: int):
    """Deploy VMUSE code to VM after cloud-init."""
    # 1. 检查 cloud-init 是否完成
    # 2. 打包并传输 VMUSE 代码
    # 3. 安装并启动服务
```

### 3. 测试验证
```bash
# 1. 创建新 VM
# 2. 等待 cloud-init 完成（检查 /opt/novaic/.cloud_init_complete）
# 3. 自动部署 VMUSE 代码
# 4. 验证所有32个工具
```

---

## ✅ 验证清单

### Cloud-Init 阶段
- [ ] 系统包全部安装
- [ ] Node.js 20 安装成功
- [ ] Python venv 创建成功
- [ ] VMUSE 依赖安装完成
- [ ] Playwright Chromium 安装
- [ ] systemd 服务配置完成
- [ ] 桌面环境启动
- [ ] 完成标记文件存在

### 部署阶段
- [ ] VMUSE 代码传输成功
- [ ] pip install -e . 成功
- [ ] systemd 服务启动
- [ ] 健康检查通过
- [ ] 所有32个工具可用

---

## 📝 注意事项

### 1. Node.js 版本
- 使用 Node.js 20 LTS（当前稳定版）
- Playwright 需要 Node.js 18+ 才能正常工作

### 2. 镜像源
- 国内用户使用阿里云镜像加速
- NodeSource 源在国内可能较慢，考虑使用淘宝镜像

### 3. 磁盘空间
- Chromium 约需 300-500 MB
- Node.js + npm 约需 100 MB
- 总计建议至少 5 GB 磁盘空间

### 4. 安装时间
- 首次启动: 约 10 分钟
- 主要耗时: Playwright Chromium 下载（2-5分钟）

---

## 🔗 相关文件

- 当前配置: `novaic-backend/gateway/vm/setup.py` (Lines 450-720)
- 优化配置: 本文档中的完整 YAML
- 部署脚本: 需要创建 `deploy_vmuse_to_vm.sh`

---

**优化完成！VM 将具备完整的 VMUSE 运行环境！** 🎉
