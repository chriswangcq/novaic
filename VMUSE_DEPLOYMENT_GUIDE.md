# VMUSE 部署完整指南

**版本**: v1.0  
**日期**: 2026-02-07  
**适用于**: NovAIC VM 环境  

---

## 🎯 部署流程概览

VMUSE 的部署分为 **3个阶段**：

```
阶段1: Cloud-Init (VM 首次启动)
  ↓
阶段2: VMUSE 代码部署 (Gateway自动 or 手动)
  ↓
阶段3: 服务启动和验证
```

---

## 📋 阶段1: Cloud-Init (自动)

### 由谁完成
- **Gateway** (`novaic-backend/gateway/vm/setup.py`)
- 在 VM 创建时自动生成 `cloud-init.iso`

### 完成的事情
1. ✅ 安装系统包（xfce4, xdotool, wmctrl, scrot等）
2. ✅ 创建 Python 虚拟环境 (`/opt/novaic/venv`)
3. ✅ 安装基础依赖（当前版本）

### 需要优化的地方 ⚠️
- ❌ **缺少 Node.js** - Playwright 需要
- ❌ **缺少完整 VMUSE 依赖** - aiohttp, pydantic-settings 等
- ❌ **Playwright Chromium 未完整安装**

### 优化方案
参考 `VMUSE_CLOUD_INIT_OPTIMIZED.md`，在 cloud-init 中添加：
```yaml
runcmd:
  # 安装 Node.js 20 LTS
  - curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  - apt-get install -y nodejs
  
  # 安装 VMUSE 完整依赖
  - /opt/novaic/venv/bin/pip install aiohttp pydantic pydantic-settings python-dotenv Pillow playwright
  
  # 安装 Playwright Chromium
  - /opt/novaic/venv/bin/playwright install --with-deps chromium
  
  # 配置 systemd 服务
  - systemctl enable novaic-vmuse
```

---

## 📦 阶段2: VMUSE 代码部署

### 当前状态
- **VMUSE 源代码位置**: `novaic-app/src-tauri/resources/novaic-mcp-vmuse/`
- **目标位置**: VM 中的 `/opt/novaic/novaic-mcp-vmuse/`

### 部署方式选项

#### 方式1: 手动部署（当前使用）✅
```bash
# 1. 打包代码
cd novaic-app/src-tauri/resources
tar -czf /tmp/novaic-mcp-vmuse.tar.gz novaic-mcp-vmuse/

# 2. 传输到 VM
scp -P 20000 /tmp/novaic-mcp-vmuse.tar.gz ubuntu@127.0.0.1:/opt/novaic/

# 3. SSH 到 VM 并解压
ssh -p 20000 ubuntu@127.0.0.1

cd /opt/novaic
tar -xzf novaic-mcp-vmuse.tar.gz

# 4. 安装依赖
cd novaic-mcp-vmuse
/opt/novaic/venv/bin/pip install -e .

# 5. 启动服务
sudo systemctl restart novaic-vmuse
sudo systemctl status novaic-vmuse
```

#### 方式2: 自动化脚本（推荐）⭐
使用 `deploy_vmuse_to_vm.sh`:
```bash
./deploy_vmuse_to_vm.sh
```

#### 方式3: Gateway 集成（未来）🔮
在 Gateway 中添加自动部署 API：
```python
@router.post("/vm/{agent_id}/deploy-vmuse")
async def deploy_vmuse(agent_id: str):
    """Deploy VMUSE code to VM after cloud-init."""
    # 1. 打包 VMUSE 代码
    # 2. SCP 传输到 VM
    # 3. SSH 安装并启动
    # 4. 验证健康状态
```

---

## 🚀 完整部署步骤（当前推荐）

### 前提条件
- ✅ VM 已创建并启动
- ✅ Cloud-init 已完成
- ✅ SSH 可访问（端口 20000）

### 步骤 1: 准备环境

```bash
cd /Users/wangchaoqun/novaic

# 确认 VM 正在运行
curl http://127.0.0.1:18080/health 2>/dev/null || echo "VM 未启动或端口未映射"

# 确认 SSH 可访问
ssh -p 20000 ubuntu@127.0.0.1 -o StrictHostKeyChecking=no 'echo "SSH 连接成功"' || sshpass -p 'ubuntu' ssh -p 20000 ubuntu@127.0.0.1 'echo "SSH 连接成功（密码认证）"'
```

### 步骤 2: 部署 VMUSE 代码

**选项 A: 使用自动化脚本**（最简单）
```bash
./deploy_vmuse_to_vm.sh
```

**选项 B: 手动部署**（更灵活）
```bash
# 1. 打包
cd novaic-app/src-tauri/resources
tar -czf /tmp/vmuse.tar.gz novaic-mcp-vmuse/

# 2. 传输
sshpass -p 'ubuntu' scp -P 20000 -o StrictHostKeyChecking=no /tmp/vmuse.tar.gz ubuntu@127.0.0.1:/opt/novaic/

# 3. 部署
sshpass -p 'ubuntu' ssh -p 20000 ubuntu@127.0.0.1 << 'EOSSH'
cd /opt/novaic
tar -xzf vmuse.tar.gz
cd novaic-mcp-vmuse
/opt/novaic/venv/bin/pip install -e .
EOSSH

# 4. 启动服务
sshpass -p 'ubuntu' ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl restart novaic-vmuse'
```

### 步骤 3: 验证部署

```bash
# 1. 检查服务状态
sshpass -p 'ubuntu' ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl status novaic-vmuse --no-pager'

# 2. 测试健康检查
curl http://127.0.0.1:18080/health

# 3. 测试所有工具
python3 /tmp/test_all_32_tools.py
```

---

## 🔧 当前部署架构

### 文件位置

**宿主机（开发机）**:
```
/Users/wangchaoqun/novaic/
├── novaic-app/src-tauri/resources/
│   └── novaic-mcp-vmuse/          ← 源代码
│       ├── src/
│       │   └── novaic_mcp_vmuse/
│       │       ├── http_server.py
│       │       └── tools/
│       ├── pyproject.toml
│       └── README.md
└── deploy_vmuse_to_vm.sh          ← 部署脚本
```

**VM（运行环境）**:
```
/opt/novaic/
├── venv/                          ← Python 虚拟环境
│   └── bin/python3
├── novaic-mcp-vmuse/              ← 部署后的代码
│   ├── src/
│   │   └── novaic_mcp_vmuse/
│   │       ├── http_server.py
│   │       └── tools/
│   └── pyproject.toml
├── .cache/                        ← Playwright Chromium
└── .dependencies_installed        ← 标记文件
```

**systemd 服务**:
```
/etc/systemd/system/novaic-vmuse.service
```

---

## 📊 部署时间线

| 阶段 | 时间 | 说明 |
|-----|------|------|
| Cloud-Init | 5-10分钟 | 系统包 + 基础依赖（首次） |
| 代码部署 | 10-30秒 | 打包、传输、安装 |
| 服务启动 | 5-10秒 | systemd 启动 + 浏览器初始化 |
| **总计** | **~6-12分钟** | 首次部署 |

**后续更新**: 仅需 20-40秒（跳过 Cloud-Init）

---

## 🎯 推荐部署方案

### 方案 A: 半自动（当前最佳）✅

**适用场景**: 开发和测试

**步骤**:
1. Gateway 创建 VM（自动 Cloud-Init）
2. 使用 `deploy_vmuse_to_vm.sh` 部署代码
3. 验证工具

**优点**:
- ✅ 简单快速
- ✅ 可随时更新代码
- ✅ 易于调试

**缺点**:
- ⚠️ 需要手动运行脚本

---

### 方案 B: 全自动（未来）🔮

**适用场景**: 生产环境

**实现方式**:
1. **优化 Cloud-Init** - 安装 Node.js + 完整依赖
2. **在 Cloud-Init 中包含 VMUSE 代码** - 通过 write_files
3. **自动启动服务** - systemd 开机启动

**步骤**:
1. 修改 `novaic-backend/gateway/vm/setup.py`
2. 在 `write_files` 中包含所有 VMUSE Python 文件
3. 在 `runcmd` 中执行 `pip install -e .`
4. VM 启动后 VMUSE 自动运行

**优点**:
- ✅ 完全自动化
- ✅ 无需额外部署步骤
- ✅ 适合生产环境

**缺点**:
- ⚠️ Cloud-init 配置变大（需要嵌入所有代码）
- ⚠️ 代码更新需要重新创建 VM

---

## 🛠️ 部署脚本详解

### deploy_vmuse_to_vm.sh

**当前版本** (已存在):
```bash
#!/bin/bash
# 部署 VMUSE 到 VM

set -e

VM_IP="127.0.0.1"
VM_PORT="20000"
VM_USER="ubuntu"
VM_PASS="ubuntu"

echo "=== VMUSE 部署脚本 ==="
echo ""

# 1. 打包代码
echo "1. 打包 VMUSE 代码..."
cd novaic-app/src-tauri/resources
tar -czf /tmp/novaic-mcp-vmuse.tar.gz novaic-mcp-vmuse/
echo "   ✅ 打包完成: /tmp/novaic-mcp-vmuse.tar.gz"

# 2. 传输到 VM
echo ""
echo "2. 传输到 VM..."
sshpass -p "$VM_PASS" scp -P $VM_PORT -o StrictHostKeyChecking=no \
  /tmp/novaic-mcp-vmuse.tar.gz $VM_USER@$VM_IP:/opt/novaic/
echo "   ✅ 传输完成"

# 3. 部署
echo ""
echo "3. 解压并安装..."
sshpass -p "$VM_PASS" ssh -p $VM_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP << 'EOSSH'
cd /opt/novaic
rm -rf novaic-mcp-vmuse  # 删除旧版本
tar -xzf novaic-mcp-vmuse.tar.gz
cd novaic-mcp-vmuse
/opt/novaic/venv/bin/pip install -e . --quiet
EOSSH
echo "   ✅ 安装完成"

# 4. 启动服务
echo ""
echo "4. 重启 VMUSE 服务..."
sshpass -p "$VM_PASS" ssh -p $VM_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP \
  'sudo systemctl restart novaic-vmuse'
sleep 3
echo "   ✅ 服务已重启"

# 5. 验证
echo ""
echo "5. 验证部署..."
SERVICE_STATUS=$(sshpass -p "$VM_PASS" ssh -p $VM_PORT -o StrictHostKeyChecking=no $VM_USER@$VM_IP \
  'sudo systemctl is-active novaic-vmuse')

if [ "$SERVICE_STATUS" = "active" ]; then
    echo "   ✅ 服务运行正常"
else
    echo "   ❌ 服务状态: $SERVICE_STATUS"
fi

# 测试健康检查
HEALTH=$(curl -s http://127.0.0.1:18080/health 2>/dev/null)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ 健康检查通过"
else
    echo "   ⚠️  健康检查失败"
fi

echo ""
echo "=== 部署完成 ==="
```

---

## 🔄 更新部署

### 场景：代码修改后重新部署

```bash
# 快速更新（推荐）
./deploy_vmuse_to_vm.sh

# 或者分步执行
cd novaic-app/src-tauri/resources
tar -czf /tmp/vmuse.tar.gz novaic-mcp-vmuse/
sshpass -p 'ubuntu' scp -P 20000 /tmp/vmuse.tar.gz ubuntu@127.0.0.1:/opt/novaic/
sshpass -p 'ubuntu' ssh -p 20000 ubuntu@127.0.0.1 << 'EOF'
cd /opt/novaic && tar -xzf vmuse.tar.gz
cd novaic-mcp-vmuse && /opt/novaic/venv/bin/pip install -e .
sudo systemctl restart novaic-vmuse
EOF
```

---

## 🎯 未来自动化方案

### 在 Gateway 中集成部署

**新增 API**: `POST /api/vm/{agent_id}/deploy-vmuse`

```python
# novaic-backend/gateway/api/vm.py

@router.post("/{agent_id}/deploy-vmuse")
async def deploy_vmuse(agent_id: str):
    """
    Deploy VMUSE code to VM after cloud-init completion.
    
    Steps:
    1. Check cloud-init completed (/opt/novaic/.dependencies_installed)
    2. Package VMUSE code from resources
    3. Transfer via SCP
    4. Install and start service
    5. Verify health
    """
    try:
        manager = get_vm_manager()
        agent = manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(404, "Agent not found")
        
        ssh_port = agent.ports.get("ssh")
        if not ssh_port:
            raise HTTPException(400, "SSH port not available")
        
        # 1. 打包代码
        import tarfile
        vmuse_src = Path(__file__).parent.parent.parent.parent / "novaic-app/src-tauri/resources/novaic-mcp-vmuse"
        tar_path = Path("/tmp") / f"vmuse-{agent_id}.tar.gz"
        
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(vmuse_src, arcname="novaic-mcp-vmuse")
        
        # 2. 传输
        subprocess.run([
            "sshpass", "-p", "ubuntu",
            "scp", "-P", str(ssh_port), "-o", "StrictHostKeyChecking=no",
            str(tar_path), f"ubuntu@127.0.0.1:/opt/novaic/"
        ], check=True)
        
        # 3. 部署
        subprocess.run([
            "sshpass", "-p", "ubuntu",
            "ssh", "-p", str(ssh_port), "-o", "StrictHostKeyChecking=no",
            "ubuntu@127.0.0.1",
            "cd /opt/novaic && tar -xzf vmuse-*.tar.gz && cd novaic-mcp-vmuse && /opt/novaic/venv/bin/pip install -e . && sudo systemctl restart novaic-vmuse"
        ], check=True)
        
        # 4. 验证
        time.sleep(3)
        vmuse_port = agent.ports.get("vmuse")
        health_resp = requests.get(f"http://127.0.0.1:{vmuse_port}/health", timeout=5)
        
        if health_resp.status_code == 200:
            return {"success": True, "message": "VMUSE deployed successfully"}
        else:
            raise Exception("Health check failed")
            
    except Exception as e:
        raise HTTPException(500, str(e))
```

---

## 📋 部署检查清单

### 部署前检查
- [ ] VM 正在运行
- [ ] SSH 端口可访问（20000）
- [ ] VMUSE 端口已映射（18080）
- [ ] Cloud-init 已完成

### 部署后检查
- [ ] 文件存在：`/opt/novaic/novaic-mcp-vmuse/`
- [ ] 服务运行：`systemctl status novaic-vmuse`
- [ ] 端口监听：`lsof -i :8080`
- [ ] 健康检查：`curl http://127.0.0.1:18080/health`
- [ ] 工具测试：`python3 /tmp/test_all_32_tools.py`

---

## 🐛 故障排查

### 问题1: SSH 连接失败
```bash
# 检查 VM 是否运行
ps aux | grep qemu

# 检查端口映射
# 查看 QEMU 命令行参数，确认 hostfwd=tcp::20000-:22
```

### 问题2: 服务启动失败
```bash
# 查看日志
ssh -p 20000 ubuntu@127.0.0.1 'sudo journalctl -u novaic-vmuse -n 50'

# 检查依赖
ssh -p 20000 ubuntu@127.0.0.1 '/opt/novaic/venv/bin/pip list | grep -E "aiohttp|playwright"'

# 检查 Node.js
ssh -p 20000 ubuntu@127.0.0.1 'node --version'
```

### 问题3: 工具调用失败
```bash
# 测试单个工具
curl -X POST http://127.0.0.1:18080/api/desktop/screenshot \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool

# 检查路由
curl http://127.0.0.1:18080/health
```

---

## 📝 关键文件位置

### 源代码
- **VMUSE 源码**: `novaic-app/src-tauri/resources/novaic-mcp-vmuse/`
- **Backend 配置**: `novaic-backend/tools_server/`
- **Gateway VM 管理**: `novaic-backend/gateway/vm/`

### 部署脚本
- **手动部署**: `deploy_vmuse_to_vm.sh`
- **自动化辅助**: `scripts/update_cloud_init_config.py`

### VM 运行时
- **代码位置**: `/opt/novaic/novaic-mcp-vmuse/`
- **虚拟环境**: `/opt/novaic/venv/`
- **服务配置**: `/etc/systemd/system/novaic-vmuse.service`
- **日志**: `journalctl -u novaic-vmuse`

---

## 🚀 快速命令参考

```bash
# ========== 部署 ==========
./deploy_vmuse_to_vm.sh                    # 一键部署

# ========== 服务管理 ==========
ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl restart novaic-vmuse'   # 重启
ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl status novaic-vmuse'    # 状态
ssh -p 20000 ubuntu@127.0.0.1 'sudo systemctl stop novaic-vmuse'      # 停止

# ========== 验证 ==========
curl http://127.0.0.1:18080/health                                    # 健康检查
python3 /tmp/test_all_32_tools.py                                     # 完整测试

# ========== 日志 ==========
ssh -p 20000 ubuntu@127.0.0.1 'sudo journalctl -u novaic-vmuse -f'   # 实时日志
ssh -p 20000 ubuntu@127.0.0.1 'sudo journalctl -u novaic-vmuse -n 50' # 最近50行

# ========== 调试 ==========
ssh -p 20000 ubuntu@127.0.0.1 'ps aux | grep http_server'            # 进程检查
ssh -p 20000 ubuntu@127.0.0.1 'sudo lsof -i :8080'                   # 端口检查
```

---

## 🎓 最佳实践

### 1. 开发流程
```bash
# 修改代码
vim novaic-app/src-tauri/resources/novaic-mcp-vmuse/src/novaic_mcp_vmuse/http_server.py

# 部署测试
./deploy_vmuse_to_vm.sh

# 验证
python3 /tmp/test_all_32_tools.py
```

### 2. 版本管理
```bash
# 在 VM 中标记版本
ssh -p 20000 ubuntu@127.0.0.1 'echo "v1.0.0" > /opt/novaic/novaic-mcp-vmuse/VERSION'

# 查看版本
ssh -p 20000 ubuntu@127.0.0.1 'cat /opt/novaic/novaic-mcp-vmuse/VERSION'
```

### 3. 备份恢复
```bash
# 备份 VM 磁盘
cp ~/.novaic/agents/{agent_id}/disk.qcow2 ~/.novaic/backups/

# 恢复
cp ~/.novaic/backups/disk.qcow2 ~/.novaic/agents/{agent_id}/
```

---

## 🎉 总结

### 当前部署方式（推荐）✅
1. Gateway 创建 VM（Cloud-Init）
2. 运行 `./deploy_vmuse_to_vm.sh`
3. 验证测试

### 优化建议
1. ✅ **更新 Cloud-Init** - 添加 Node.js + 完整依赖（参考 VMUSE_CLOUD_INIT_OPTIMIZED.md）
2. 🔮 **集成到 Gateway** - 添加自动部署 API
3. 🔮 **监控和告警** - 添加服务健康监控

---

**📚 相关文档**:
- [Cloud-Init 优化方案](./VMUSE_CLOUD_INIT_OPTIMIZED.md)
- [完整认证报告](./VMUSE_ALL_32_TOOLS_FINAL_CERTIFICATION.md)
- [集成完成报告](./VMUSE_INTEGRATION_COMPLETE.md)

**✅ 当前部署流程已验证可用，推荐使用半自动方案（Cloud-Init + 部署脚本）**
