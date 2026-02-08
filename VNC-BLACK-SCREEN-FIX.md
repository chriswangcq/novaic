# VNC 黑屏问题修复总结

## 问题现象

使用 QEMU native VNC 连接虚拟机时，VNC 客户端能够连接成功，但显示黑屏。

## 根本原因

**架构不匹配：**

```
QEMU native VNC 的显示链路：
X Server → virtio-gpu → QEMU VNC Server → VNC 客户端

问题配置：
X Server (dummy 驱动) → [不输出到任何设备] → virtio-gpu [空] → QEMU VNC → 黑屏
```

**核心原因：**
- QEMU native VNC 显示的是 **virtio-gpu 虚拟显卡的输出**
- 之前的配置使用 **`dummy` 驱动**作为 X Server 的显示驱动
- `dummy` 驱动是一个"假驱动"，**不会输出到任何实际显示设备**（包括 virtio-gpu）
- 结果：virtio-gpu 没有接收到任何图形输出，VNC 自然是黑屏

## 与 x11vnc 的区别

```
旧方案（x11vnc）：
  X Server (任何驱动) → X 帧缓冲 
                         ↓
                      x11vnc 直接读取 → VNC 客户端 ✅
  
  特点：x11vnc 直接从 X Server 的帧缓冲读取，不依赖硬件显卡

新方案（QEMU native VNC）：
  X Server (dummy) → [不输出] → virtio-gpu [空] → QEMU VNC → VNC 客户端 ❌
  X Server (modesetting) → virtio-gpu → QEMU VNC → VNC 客户端 ✅
  
  特点：QEMU VNC 从虚拟显卡 (virtio-gpu) 读取，需要 X Server 输出到显卡
```

## 解决方案

**核心修改：将 X Server 驱动从 `dummy` 改为 `modesetting`**

### 1. 修改 Xorg 配置

**文件：** `/etc/X11/xorg.conf.d/10-novaic.conf`

```diff
  Section "Device"
    Identifier "VirtioGPU"
-   Driver "dummy"
+   Driver "modesetting"
+   Option "AccelMethod" "glamor"
  EndSection
```

### 2. modesetting 驱动的优势

- **现代通用驱动**：支持所有 KMS (Kernel Mode Setting) 显卡
- **virtio-gpu 兼容**：正确输出到 QEMU 虚拟显卡
- **硬件加速**：支持 glamor 加速（基于 OpenGL）
- **无需额外包**：包含在 `xserver-xorg-core` 中

### 3. 验证驱动加载

```bash
# 检查 X Server 日志
cat /var/log/Xorg.0.log | grep -E 'modesetting|Loading.*driver'

# 应该看到：
# (II) LoadModule: "modesetting"
# (II) Loading /usr/lib/xorg/modules/drivers/modesetting_drv.so
# (II) modesetting: Driver for Modesetting Kernel Drivers: kms
```

### 4. 验证显卡驱动

```bash
# 检查 virtio-gpu 内核模块
lsmod | grep virtio

# 应该看到：
# virtio_gpu             94208  0
# virtio_dma_buf         12288  1 virtio_gpu
```

## 修复文件

**修改文件：** `novaic-backend/gateway/vm/setup.py`

**修改位置：** Line 521-537 (write_files 部分的 X Server 配置)

```python
# X Server 配置（使用 modesetting 驱动连接到 virtio-gpu）
- path: /etc/X11/xorg.conf.d/10-novaic.conf
  content: |
    Section "Device"
      Identifier "VirtioGPU"
      Driver "modesetting"
      Option "AccelMethod" "glamor"
    EndSection
    Section "Screen"
      Identifier "DefaultScreen"
      Device "VirtioGPU"
      DefaultDepth 24
      SubSection "Display"
        Depth 24
        Modes "1280x720" "1024x768"
      EndSubSection
    EndSection
  permissions: '0644'
```

## 手动修复已存在的 VM

如果有已经创建的 VM 需要修复：

```bash
# 1. SSH 到 VM
ssh -i ~/.ssh/id_xxx -p PORT ubuntu@localhost

# 2. 更新 Xorg 配置
sudo tee /etc/X11/xorg.conf.d/10-novaic.conf <<'EOF'
Section "Device"
  Identifier "VirtioGPU"
  Driver "modesetting"
  Option "AccelMethod" "glamor"
EndSection
Section "Screen"
  Identifier "DefaultScreen"
  Device "VirtioGPU"
  DefaultDepth 24
  SubSection "Display"
    Depth 24
    Modes "1280x720" "1024x768"
  EndSubSection
EndSection
EOF

# 3. 重启 LightDM
sudo systemctl restart lightdm

# 4. 等待 3-5 秒后，VNC 应该能正常显示桌面
```

## 测试验证

1. 创建新的 Agent（会自动使用新配置）
2. 等待 cloud-init 完成
3. 通过 VNC 连接（UI 中的 "Desktop" 按钮）
4. 应该能够看到 XFCE4 桌面环境

## 技术要点

### QEMU VNC 显示链路

```
┌─────────────┐
│  VM 内部    │
│             │
│  X Server   │ 输出图形
│     ↓       │
│ virtio-gpu  │ 虚拟显卡
└─────────────┘
      ↓
┌─────────────┐
│  QEMU       │
│             │
│ VNC Server  │ 读取 virtio-gpu
└─────────────┘
      ↓
  VNC 客户端
```

### 关键概念

- **virtio-gpu**：QEMU 提供的准虚拟化 GPU 设备
- **modesetting**：Linux 通用显示驱动，使用 KMS
- **KMS (Kernel Mode Setting)**：内核层面的显示模式设置
- **glamor**：基于 OpenGL 的 2D 加速框架

## 日期

2026-02-08

## 状态

✅ 已修复并验证
