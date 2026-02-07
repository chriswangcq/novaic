# Cloud-Init 完整依赖清单

## 概述

所有依赖已移至 cloud-init 阶段安装，无需单独的"部署阶段"。

文件位置: `novaic-backend/gateway/vm/setup.py`

---

## 1. 系统包 (packages)

### 桌面环境
- `xfce4` - 轻量级桌面环境
- `xfce4-terminal` - XFCE 终端模拟器
- `xfce4-goodies` - XFCE 附加工具
- `lightdm` - 显示管理器
- `lightdm-gtk-greeter` - LightDM GTK greeter
- `dbus-x11` - D-Bus X11 支持
- `xvfb` - 虚拟帧缓冲 X 服务器

### 浏览器和工具
- `chromium-browser` - Chromium 浏览器
- `xdotool` - X11 自动化工具 (Mouse/Keyboard/Window 控制)
- `wmctrl` - 窗口管理器控制 (Window 工具)
- `scrot` - 截图工具 (Screenshot 功能)
- `imagemagick` - 图像处理工具
- `xclip` - 剪贴板工具 (Clipboard 功能)

### Python 环境
- `python3` - Python 3 运行时
- `python3-pip` - Python 包管理器
- `python3-venv` - Python 虚拟环境

### 基础工具
- `curl` - HTTP 客户端
- `wget` - 文件下载工具
- `net-tools` - 网络工具
- `openssh-server` - SSH 服务器
- `git` - 版本控制
- `vim` - 文本编辑器
- `htop` - 进程监控

### VM 集成
- `qemu-guest-agent` - QEMU Guest Agent (VM 管理)

---

## 2. Python 包 (runcmd)

### Playwright (浏览器自动化)
```bash
sudo -u ubuntu pip3 install --user playwright
sudo -u ubuntu python3 -m playwright install chromium
sudo -u ubuntu python3 -m playwright install-deps chromium
```

**说明**:
- 使用 `--user` 安装到用户环境 (`/home/ubuntu/.local`)
- `install chromium` 下载 Chromium 浏览器二进制
- `install-deps` 安装 Chromium 系统依赖
- 安装时间: 约 2-5 分钟 (首次启动时)

---

## 3. 脚本文件 (write_files)

### Playwright Helper 脚本
- **路径**: `/opt/novaic/scripts/playwright_helper.py`
- **权限**: `0755` (可执行)
- **所有者**: `ubuntu:ubuntu`
- **功能**: Browser 控制脚本,支持:
  - `navigate` - 导航到 URL
  - `click` - 点击元素
  - `type` - 输入文本
  - `screenshot` - 截图
  - `content` - 获取页面内容

### 配置文件
- `/etc/lightdm/lightdm.conf.d/50-autologin.conf` - 自动登录配置
- `/home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml` - 电源管理配置

---

## 4. Runcmd 执行顺序

```yaml
runcmd:
  # 1. 设置目录权限
  - chown -R ubuntu:ubuntu /home/ubuntu
  - mkdir -p /home/ubuntu/.config/xfce4/xfconf/xfce-perchannel-xml
  - chown -R ubuntu:ubuntu /home/ubuntu/.config
  - mkdir -p /opt/novaic/scripts
  - chown -R ubuntu:ubuntu /opt/novaic
  
  # 2. 等待网络连接
  - echo "Waiting for network..."
  - until ping -c 1 -W 3 8.8.8.8 > /dev/null 2>&1; do sleep 2; done
  - echo "Network ready."
  
  # 3. 启用 QEMU Guest Agent
  - systemctl daemon-reload
  - systemctl enable qemu-guest-agent
  - systemctl start qemu-guest-agent
  
  # 4. 安装 Playwright (关键新增)
  - echo "Installing Playwright..."
  - sudo -u ubuntu pip3 install --user playwright
  - sudo -u ubuntu python3 -m playwright install chromium
  - sudo -u ubuntu python3 -m playwright install-deps chromium
  - echo "Playwright installation completed."
  
  # 5. 启动显示管理器
  - systemctl enable lightdm
  - systemctl start lightdm
  - sleep 10
  
  # 6. 标记安装完成
  - touch /opt/novaic/.dependencies_installed
  - echo "NovAIC VM cloud-init completed at $(date)" > /var/log/novaic-init-done.log
```

---

## 5. 工具依赖映射

| 工具类别 | 系统包 | Python 包 | 脚本文件 |
|---------|--------|-----------|---------|
| **Mouse** | xdotool | - | - |
| **Keyboard** | xdotool | - | - |
| **Window** | xdotool, wmctrl | - | - |
| **Clipboard** | xclip | - | - |
| **Screenshot** | scrot, imagemagick | - | - |
| **Browser** | chromium-browser | playwright | playwright_helper.py |
| **Desktop** | xfce4, lightdm, xvfb | - | - |
| **VM 管理** | qemu-guest-agent | - | - |

---

## 6. 验证检查点

### ✅ 已完成
- [x] 所有系统包都在 `packages` 列表中
- [x] Playwright 安装添加到 `runcmd`
- [x] playwright_helper.py 在 `write_files` 中
- [x] 安装完成标记 (`/opt/novaic/.dependencies_installed`)
- [x] Python 语法验证通过
- [x] 执行顺序合理 (网络 → Guest Agent → Playwright → Display)

### 📋 关键特性
- **无需手动部署**: VM 启动后自动完成所有安装
- **用户环境隔离**: Playwright 安装在 ubuntu 用户环境
- **完成标记**: 可通过检查 `/opt/novaic/.dependencies_installed` 确认安装状态
- **日志记录**: 完成时间记录在 `/var/log/novaic-init-done.log`

---

## 7. 预期时间线

| 阶段 | 时间 | 说明 |
|-----|------|------|
| 系统包安装 | ~2-3 分钟 | apt install packages |
| 网络等待 | ~5-10 秒 | 等待网络连接 |
| Guest Agent 启动 | ~2-3 秒 | systemctl start |
| Playwright 安装 | ~2-5 分钟 | pip + chromium 下载 |
| Display 启动 | ~10 秒 | lightdm 启动 |
| **总计** | **~5-10 分钟** | 首次启动 |

**后续启动**: ~30-60 秒 (无需重新安装)

---

## 8. 镜像源配置

支持国内镜像加速 (通过 `use_cn_mirrors` 参数):

### APT 镜像
- **国内**: `mirrors.aliyun.com/ubuntu` (或 `ubuntu-ports` for ARM)
- **国际**: `archive.ubuntu.com/ubuntu` (或 `ports.ubuntu.com` for ARM)

### PIP 镜像
- **国内**: `mirrors.aliyun.com/pypi/simple/`
- **国际**: `pypi.org/simple/`

---

## 9. 故障排查

### 检查安装状态
```bash
# SSH 进入 VM
ssh ubuntu@<vm-ip>

# 检查安装完成标记
ls -la /opt/novaic/.dependencies_installed

# 检查 Playwright 安装
python3 -m playwright --version

# 检查 Chromium 浏览器
ls ~/.local/share/ms-playwright/

# 查看 cloud-init 日志
sudo cat /var/log/cloud-init-output.log
```

### 常见问题
1. **Playwright 安装失败**: 检查网络连接和 pip 镜像配置
2. **Chromium 依赖缺失**: `playwright install-deps` 会自动安装
3. **权限问题**: 确保使用 `sudo -u ubuntu` 安装

---

## 总结

✅ **所有依赖已完全集成到 cloud-init 配置中**  
✅ **无需单独的"部署阶段"**  
✅ **VM 首次启动自动完成全部安装**  
✅ **配置文件经过 Python 语法验证**

文件位置: `novaic-backend/gateway/vm/setup.py` (Lines 460-700)
