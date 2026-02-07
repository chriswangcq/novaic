# VMUSE Setup.py 优化说明

**版本**: v2.0  
**日期**: 2026-02-07  
**状态**: ✅ 已完成

---

## 🎯 优化目标

使 VM 在首次启动时（Cloud-Init）自动完成所有 VMUSE 依赖安装，无需额外部署步骤。

---

## 📝 完成的修改

### 文件: `novaic-backend/gateway/vm/setup.py`

#### 修改 1: 增强的 runcmd 阶段

**原来的流程**（5个阶段）:
```yaml
1. 创建目录
2. 安装 Playwright
3. 设置权限
4. 启动显示管理器
5. 标记完成
```

**新的流程**（11个阶段）✅:
```yaml
Phase 1: Directory Setup
  - 创建所有必要目录（包括 /opt/novaic/novaic-mcp-vmuse/）

Phase 2: Network & Environment
  - 等待网络
  - 配置环境变量（DISPLAY, PATH）

Phase 3: Node.js Installation ⭐ 新增
  - 安装 Node.js 20 LTS
  - 记录版本信息

Phase 4: Python Virtual Environment
  - 创建 venv
  - 升级 pip

Phase 5: VMUSE Python Dependencies ⭐ 扩展
  - 安装 aiohttp, pydantic, pydantic-settings
  - 安装 python-dotenv, Pillow
  - 安装 playwright

Phase 6: Playwright + Chromium
  - 安装 Chromium 浏览器及系统依赖

Phase 7: QEMU Guest Agent
  - 启用 QEMU Guest Agent

Phase 8: Ownership
  - 设置正确的文件权限

Phase 9: Display Manager
  - 启动 lightdm

Phase 10: Enable VMUSE Service ⭐ 新增
  - 启用 systemd 服务（等待代码部署后自动启动）

Phase 11: Completion
  - 创建完成标记文件
```

#### 修改 2: systemd 服务定义

**新增的 write_files 条目**:
```yaml
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
```

---

## 📊 依赖对比

### 之前（缺失的依赖）❌
- ❌ Node.js（Playwright 需要）
- ❌ aiohttp（VMUSE HTTP 服务器）
- ❌ pydantic-settings（配置管理）
- ❌ python-dotenv（环境变量）
- ❌ Pillow（图像处理）
- ❌ systemd 服务配置

### 现在（完整依赖）✅
- ✅ Node.js 20 LTS
- ✅ aiohttp
- ✅ pydantic + pydantic-settings
- ✅ python-dotenv
- ✅ Pillow
- ✅ playwright + Chromium
- ✅ systemd 服务（已配置）

---

## 🚀 部署流程变化

### 之前的部署流程
```
1. 创建 VM（Gateway）
   └─> Cloud-Init 安装基础依赖（5-10分钟）
   
2. 等待 Cloud-Init 完成

3. 手动部署 VMUSE 代码 ⚠️
   $ ./deploy_vmuse.sh
   └─> 打包、传输、安装（30-60秒）
   
4. 验证工具
```

### 新的部署流程（优化后）
```
1. 创建 VM（Gateway）
   └─> Cloud-Init 安装所有依赖 + Node.js（6-12分钟）
   
2. 等待 Cloud-Init 完成

3. 部署 VMUSE 代码 ✅（仍需手动，但更快）
   $ ./deploy_vmuse.sh
   └─> 只需打包和传输（20-30秒）
   └─> 依赖已安装，无需额外 pip install
   
4. 服务自动启动（systemd）✅
   
5. 验证工具
```

### 未来的自动化部署（待实现）🔮
```
1. 创建 VM（Gateway）
   └─> Cloud-Init 安装所有依赖 + VMUSE 代码（嵌入）
   
2. 等待 Cloud-Init 完成

3. VMUSE 自动运行 ✅
   └─> systemd 自动启动
   
4. 验证工具
```

---

## ⏱️ 时间对比

| 阶段 | 之前 | 现在 | 未来（全自动）|
|-----|-----|-----|-------------|
| Cloud-Init | 5-10分钟 | 6-12分钟 | 8-15分钟 |
| 代码部署 | 30-60秒（手动）| 20-30秒（手动）| 0秒（自动）|
| 服务启动 | 5-10秒（手动）| 自动 | 自动 |
| **总计** | **6-11分钟** | **7-13分钟** | **8-15分钟** |

> **注意**: 虽然新流程时间稍长（+1-2分钟），但手动步骤大幅减少。

---

## 🧪 测试计划

### 测试步骤

#### 1. 备份现有 VM
```bash
# 如果有运行中的 VM，先备份
cp ~/.novaic/agents/{agent_id}/disk.qcow2 ~/.novaic/backups/
```

#### 2. 创建新 VM
```bash
# 通过 UI 或 API 创建新 VM
# 使用更新后的 setup.py 配置
```

#### 3. 监控 Cloud-Init
```bash
# SSH 到 VM
ssh -p 20000 ubuntu@127.0.0.1

# 查看 cloud-init 进度
tail -f /var/log/cloud-init-output.log

# 或查看分阶段日志
journalctl -u cloud-init -f
```

#### 4. 验证依赖安装
```bash
ssh -p 20000 ubuntu@127.0.0.1 << 'EOF'
echo "=== 验证安装 ==="

echo "1. Node.js:"
node --version
npm --version

echo ""
echo "2. Python 依赖:"
/opt/novaic/venv/bin/pip list | grep -E "aiohttp|pydantic|playwright|Pillow|dotenv"

echo ""
echo "3. Playwright Chromium:"
/opt/novaic/venv/bin/playwright show | grep chromium

echo ""
echo "4. systemd 服务:"
systemctl list-unit-files | grep novaic-vmuse

echo ""
echo "5. 目录结构:"
ls -la /opt/novaic/

echo ""
echo "6. 完成标记:"
ls -la /opt/novaic/.cloud_init_complete
ls -la /opt/novaic/.dependencies_installed
EOF
```

#### 5. 部署 VMUSE 代码
```bash
./deploy_vmuse.sh
```

#### 6. 验证服务
```bash
# 检查服务状态
ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl status novaic-vmuse'

# 健康检查
curl http://127.0.0.1:18080/health

# 完整工具测试
python3 /tmp/test_all_32_tools.py
```

---

## ✅ 预期结果

### Cloud-Init 完成后应有：
- ✅ Node.js 20.x 已安装
- ✅ Python venv 创建并包含所有依赖
- ✅ Playwright Chromium 已安装
- ✅ `/opt/novaic/novaic-mcp-vmuse/` 目录存在（空）
- ✅ `/etc/systemd/system/novaic-vmuse.service` 文件存在
- ✅ 服务已启用但未运行（等待代码部署）
- ✅ `/opt/novaic/.cloud_init_complete` 标记文件存在

### 部署 VMUSE 后应有：
- ✅ `/opt/novaic/novaic-mcp-vmuse/src/` 代码存在
- ✅ `novaic-vmuse.service` 运行中
- ✅ 端口 8080 监听（VM 内部）
- ✅ 健康检查通过
- ✅ 所有 32 个工具可用

---

## 🐛 故障排查

### 问题 1: Cloud-Init 失败

**症状**:
```
ssh -p 20000 ubuntu@127.0.0.1 'cat /opt/novaic/.cloud_init_complete'
# 文件不存在
```

**排查步骤**:
```bash
# 查看 cloud-init 日志
ssh -p 20000 ubuntu@127.0.0.1 'tail -100 /var/log/cloud-init-output.log'

# 查看是否有错误
ssh -p 20000 ubuntu@127.0.0.1 'journalctl -u cloud-init | grep -i error'
```

**常见原因**:
- 网络超时（Node.js 下载失败）
- 镜像源问题（pip install 失败）
- 磁盘空间不足

---

### 问题 2: Node.js 未安装

**症状**:
```bash
ssh -p 20000 ubuntu@127.0.0.1 'node --version'
# Command not found
```

**排查**:
```bash
# 检查 cloud-init runcmd 日志
ssh -p 20000 ubuntu@127.0.0.1 'cat /var/log/cloud-init-output.log | grep -A 20 "Phase 3"'

# 手动安装
ssh -p 20000 ubuntu@127.0.0.1 << 'EOF'
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
EOF
```

---

### 问题 3: systemd 服务未启动

**症状**:
```bash
ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl status novaic-vmuse'
# Unit not found or inactive
```

**排查**:
```bash
# 检查服务文件
ssh -p 20000 ubuntu@127.0.0.1 'cat /etc/systemd/system/novaic-vmuse.service'

# 检查代码是否部署
ssh -p 20000 ubuntu@127.0.0.1 'ls -la /opt/novaic/novaic-mcp-vmuse/src/'

# 手动启动
ssh -p 20000 ubuntu@127.0.0.1 << 'EOF'
sudo systemctl daemon-reload
sudo systemctl enable novaic-vmuse
sudo systemctl start novaic-vmuse
sudo systemctl status novaic-vmuse
EOF
```

---

## 📋 回滚方案

如果新配置有问题，可以回滚到旧版本：

### 回滚 setup.py
```bash
cd /Users/wangchaoqun/novaic
git diff novaic-backend/gateway/vm/setup.py
git checkout novaic-backend/gateway/vm/setup.py
```

### 使用备份的 VM
```bash
# 如果已创建新 VM 但有问题，恢复备份
rm ~/.novaic/agents/{agent_id}/disk.qcow2
cp ~/.novaic/backups/disk.qcow2 ~/.novaic/agents/{agent_id}/
```

---

## 🎯 关键改进点

### 1. Node.js 自动安装 ⭐
**影响**: Playwright 浏览器依赖 Node.js 运行时
**好处**: 无需手动安装，减少部署错误

### 2. 完整 Python 依赖 ⭐
**影响**: VMUSE HTTP 服务器需要 aiohttp, pydantic 等
**好处**: 
- `./deploy_vmuse.sh` 更快（无需 pip install）
- 减少网络依赖

### 3. systemd 服务配置 ⭐
**影响**: 服务自动管理
**好处**:
- 开机自启
- 自动重启（出错后）
- 统一日志管理（journalctl）

### 4. 分阶段日志 ⭐
**影响**: Cloud-Init 执行过程更清晰
**好处**:
- 易于调试
- 快速定位失败阶段
- 更好的用户体验

---

## 🚀 后续优化方向

### 短期（已完成）✅
- ✅ Node.js 安装
- ✅ 完整依赖
- ✅ systemd 服务
- ✅ 分阶段日志

### 中期（可选）
- 🔲 在 Cloud-Init 中嵌入 VMUSE 代码（通过 write_files）
- 🔲 Gateway 自动部署 API
- 🔲 健康检查和监控

### 长期（规划）
- 🔲 镜像预构建（包含所有依赖的自定义镜像）
- 🔲 多 VM 管理（并发创建、批量部署）
- 🔲 滚动更新（零停机更新）

---

## 📚 相关文档

- [完整部署指南](./VMUSE_DEPLOYMENT_GUIDE.md)
- [Cloud-Init 优化方案](./VMUSE_CLOUD_INIT_OPTIMIZED.md)
- [32 工具认证报告](./VMUSE_ALL_32_TOOLS_FINAL_CERTIFICATION.md)

---

## 🎉 总结

### 优化成果
- ✅ Cloud-Init 配置完整化（11个阶段）
- ✅ 所有依赖自动安装（Node.js + Python）
- ✅ systemd 服务自动配置
- ✅ 部署时间缩短（依赖预安装）
- ✅ 更好的可维护性和可调试性

### 建议测试
1. 创建新 VM 验证 Cloud-Init
2. 使用 `./deploy_vmuse.sh` 部署代码
3. 运行 `test_all_32_tools.py` 完整测试

### 下一步
- 测试新配置
- 根据测试结果调整
- 考虑实现 Gateway 自动部署 API

---

**状态**: ✅ 代码已更新，等待测试
**更新时间**: 2026-02-07
