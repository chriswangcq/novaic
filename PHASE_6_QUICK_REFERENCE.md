# Phase 6 快速参考 - FastMCP 替代方案

**快速导航**: [完整设计文档](./PHASE_6_FASTMCP_REPLACEMENT_DESIGN.md)

---

## 🎯 一句话总结

**用 Guest Agent + vmcontrol 替代 VM 内的 FastMCP/VMUSE，实现轻量化、高性能的 VM 工具集成。**

---

## 📊 核心对比

| 方面 | FastMCP/VMUSE | vmcontrol 方案 | 改进 |
|------|---------------|----------------|------|
| **架构** | VM 内 MCP 服务器 | 宿主机 vmcontrol | ✅ 更可控 |
| **依赖** | Python + FastMCP | 仅 qemu-ga | ✅ -90MB |
| **性能** | ~200ms | ~100ms | ✅ 快 2x |
| **并发** | ~10 req/s | ~50 req/s | ✅ 强 5x |

---

## 📋 功能映射速查

### ✅ 已实现（无需迁移）

| VMUSE 工具 | 实现方式 | 备注 |
|-----------|---------|------|
| `screenshot` | QMP screendump | Phase 3.2 |
| `mouse` | QMP input-send-event | Phase 3.3 |
| `keyboard` | QMP input-send-event | Phase 3.3 |
| `run_command` | Guest Agent exec | Phase 3.1 |
| `read_file` | Guest Agent file-read | Phase 3.1 |
| `write_file` | Guest Agent file-write | Phase 3.1 |

### 🔄 需迁移（浏览器）

| VMUSE 工具 | 实现方式 | 优先级 |
|-----------|---------|--------|
| `browser_navigate` | Playwright CLI | P1 |
| `browser_click` | Playwright CLI | P1 |
| `browser_type` | Playwright CLI | P1 |
| `browser_screenshot` | Playwright CLI | P1 |
| `browser_eval` | Playwright CLI | P2 |
| `browser_scroll` | Playwright CLI | P2 |
| `browser_*_tab` | Playwright CLI | P2 |

### ⚡ 易实现（封装）

| VMUSE 工具 | 实现方式 | 命令 |
|-----------|---------|------|
| `list_files` | Guest Agent exec | `ls -la` |
| `file_info` | Guest Agent exec | `stat` |
| `run_python` | Guest Agent exec | `python3 -c` |
| `list_windows` | Guest Agent exec | `wmctrl -l` |
| `focus_window` | Guest Agent exec | `wmctrl -a` |
| `launch_app` | Guest Agent exec | 直接启动 |
| `clipboard_get` | Guest Agent exec | `xclip -o` |
| `clipboard_set` | Guest Agent exec | `xclip -i` |

---

## 🏗️ API 速查

### 浏览器操作

```bash
# 导航
POST /api/vms/{vm_id}/browser/navigate
{"url": "https://example.com", "wait_until": "load"}

# 点击
POST /api/vms/{vm_id}/browser/click
{"selector": "#login-button", "timeout": 5000}

# 输入
POST /api/vms/{vm_id}/browser/type
{"selector": "input[name='user']", "text": "admin", "clear": true}

# 截图
GET /api/vms/{vm_id}/browser/screenshot?full_page=false

# 执行 JS
POST /api/vms/{vm_id}/browser/eval
{"script": "document.title"}
```

### 文件操作（扩展）

```bash
# 列出目录（新增）
GET /api/vms/{vm_id}/guest/files?path=/home/ubuntu

# 文件信息（新增）
GET /api/vms/{vm_id}/guest/files/info?path=/tmp/test.txt

# 删除文件（新增）
DELETE /api/vms/{vm_id}/guest/files?path=/tmp/test.txt
```

### Shell 操作（扩展）

```bash
# 执行 Python（新增）
POST /api/vms/{vm_id}/guest/exec/python
{"code": "print('Hello')", "wait": true}
```

### 窗口操作（新增）

```bash
# 列出窗口
GET /api/vms/{vm_id}/windows

# 聚焦窗口
POST /api/vms/{vm_id}/windows/{window_id}/focus

# 启动应用
POST /api/vms/{vm_id}/windows/launch
{"app": "firefox"}
```

### 环境感知（新增）

```bash
# 系统快照
GET /api/vms/{vm_id}/system/snapshot

# 目录快照
GET /api/vms/{vm_id}/system/directory?path=/home/ubuntu&depth=3

# 剪贴板
GET /api/vms/{vm_id}/system/clipboard
POST /api/vms/{vm_id}/system/clipboard
{"content": "new text"}

# 环境信息
GET /api/vms/{vm_id}/system/environment
```

---

## 🔧 实现方案

### 推荐方案：混合架构

```
Gateway → vmcontrol → { QMP (桌面/截图)
                      { Guest Agent → { Shell/文件
                                      { Playwright CLI (浏览器)
```

**为什么保留 Playwright?**
- ✅ 需要 CSS 选择器（无法用坐标替代）
- ✅ 需要 DOM 访问和 JavaScript 执行
- ✅ 功能完整，易于迁移
- ❌ 仅用 QMP 输入会严重退化用户体验

---

## 📅 实施计划

| 阶段 | 时间 | 任务 |
|------|------|------|
| **6.1** | 2-3 天 | 核心封装（文件/Shell/窗口） |
| **6.2** | 3-4 天 | 浏览器集成（Playwright CLI） |
| **6.3** | 2-3 天 | 环境感知（系统/目录快照） |
| **6.4** | 1-2 天 | Gateway 适配层 |
| **6.5** | 1 天 | 清理 FastMCP |
| **迁移** | 2-3 周 | 并行运行 + 验证 |

**总时间**: 约 **5 周**

---

## 📈 性能提升

| 操作 | 改进 | 数值 |
|------|------|------|
| 文件读取 | ✅ 快 2x | 200ms → 100ms |
| 命令执行 | ✅ 快 2x | 300ms → 150ms |
| 截图 | ✅ 快 2x | 400ms → 200ms |
| 鼠标点击 | ✅ 快 10x | 200ms → 20ms |
| 并发能力 | ✅ 强 5x | 10 req/s → 50 req/s |
| VM 内存 | ✅ 省 90MB | 4100MB → 4010MB |

---

## 🚀 快速开始

### 1. 开发环境设置

```bash
# 进入 vmcontrol 目录
cd novaic-app/src-tauri/vmcontrol

# 运行测试
cargo test --all-features

# 启动 vmcontrol 服务
cargo run -- --vm-id 1 --qmp-socket /tmp/novaic/novaic-qmp-1.sock \
             --ga-socket /tmp/novaic/novaic-ga-1.sock
```

### 2. 测试新 API

```bash
# 文件列表（Phase 6.1 待实现）
curl http://localhost:8000/api/vms/1/guest/files?path=/home/ubuntu

# 执行 Python（Phase 6.1 待实现）
curl -X POST http://localhost:8000/api/vms/1/guest/exec/python \
  -H "Content-Type: application/json" \
  -d '{"code": "print(1+1)", "wait": true}'

# 浏览器导航（Phase 6.2 待实现）
curl -X POST http://localhost:8000/api/vms/1/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### 3. VM 准备（Phase 6.2）

```bash
# 在 VM 内部安装 Playwright CLI 脚本
sudo cp novaic-vm/scripts/pw-* /usr/local/bin/
sudo chmod +x /usr/local/bin/pw-*

# 测试脚本
/usr/local/bin/pw-navigate https://example.com
```

---

## 🔍 故障排查

### Guest Agent 连接失败

```bash
# 检查 Guest Agent 是否运行
ps aux | grep qemu-ga

# 检查 socket 文件
ls -la /tmp/novaic/novaic-ga-*.sock

# 手动测试连接
echo '{"execute":"guest-ping"}' | nc -U /tmp/novaic/novaic-ga-1.sock

# 查看日志
journalctl -u qemu-guest-agent -f
```

### 浏览器操作失败

```bash
# 检查 Playwright 安装
which playwright
playwright --version

# 检查 Chrome 是否运行
ps aux | grep chromium

# 测试 CDP 端口
curl http://localhost:9222/json/version

# 手动测试脚本
/usr/local/bin/pw-navigate https://example.com
```

### 性能问题

```bash
# 查看 vmcontrol 资源使用
top -p $(pgrep vmcontrol)

# 查看 Guest Agent 延迟
time echo '{"execute":"guest-ping"}' | nc -U /tmp/novaic/novaic-ga-1.sock

# 压力测试
ab -n 1000 -c 10 http://localhost:8000/api/vms/1/guest/files?path=/tmp
```

---

## 📂 关键文件位置

### vmcontrol 源码

```
novaic-app/src-tauri/vmcontrol/src/
├── api/
│   ├── routes/
│   │   ├── guest.rs          # Guest Agent API (已有)
│   │   ├── browser.rs         # 浏览器 API (6.2 新增)
│   │   ├── system.rs          # 环境感知 API (6.3 新增)
│   │   └── screen.rs          # 截图 API (已有)
│   └── types.rs               # API 类型定义
├── qemu/
│   ├── guest_agent.rs         # Guest Agent 客户端
│   └── qmp.rs                 # QMP 客户端
└── main.rs
```

### VM 脚本

```
novaic-vm/scripts/
├── pw-navigate               # Playwright 导航 (6.2 新增)
├── pw-click                  # Playwright 点击 (6.2 新增)
├── pw-type                   # Playwright 输入 (6.2 新增)
├── pw-screenshot             # Playwright 截图 (6.2 新增)
└── install-playwright-cli.sh # 安装脚本 (6.2 新增)
```

### Gateway 适配层

```
novaic-backend/gateway/clients/
├── vmcontrol.py              # vmcontrol HTTP 客户端 (已有)
└── vmcontrol_adapter.py      # MCP 适配层 (6.4 新增)
```

---

## ⚠️ 风险提示

### 高风险

| 风险 | 缓解措施 |
|------|---------|
| 浏览器功能退化 | ✅ 保留 Playwright，充分测试 |
| 迁移期间不稳定 | ✅ 并行运行，灰度切换 |

### 中风险

| 风险 | 缓解措施 |
|------|---------|
| Guest Agent 连接失败 | 重试机制，健康检查 |
| 命令执行超时 | 超时配置，异步执行 |

---

## 📚 相关文档

- [完整设计文档](./PHASE_6_FASTMCP_REPLACEMENT_DESIGN.md)
- [Phase 3.1 - Guest Agent](./novaic-app/src-tauri/vmcontrol/PHASE_3_1_COMPLETION_REPORT.md)
- [Phase 3.2 - QMP 截图](./novaic-app/src-tauri/vmcontrol/PHASE_3_2_COMPLETION_REPORT.md)
- [Phase 3.3 - QMP 输入](./novaic-app/src-tauri/vmcontrol/PHASE_3.3_SUMMARY.md)

---

## ✅ 检查清单

### Phase 6.1 - 核心封装

- [ ] `GET /api/vms/:id/guest/files`
- [ ] `GET /api/vms/:id/guest/files/info`
- [ ] `DELETE /api/vms/:id/guest/files`
- [ ] `POST /api/vms/:id/guest/exec/python`
- [ ] `GET /api/vms/:id/windows`
- [ ] `POST /api/vms/:id/windows/:id/*`
- [ ] `POST /api/vms/:id/windows/launch`
- [ ] 单元测试 + 集成测试

### Phase 6.2 - 浏览器集成

- [ ] Playwright CLI 脚本 (pw-*)
- [ ] VM 安装脚本
- [ ] `POST /api/vms/:id/browser/navigate`
- [ ] `POST /api/vms/:id/browser/click`
- [ ] `POST /api/vms/:id/browser/type`
- [ ] `GET /api/vms/:id/browser/screenshot`
- [ ] `POST /api/vms/:id/browser/eval`
- [ ] `POST /api/vms/:id/browser/scroll`
- [ ] `GET /api/vms/:id/browser/tabs`
- [ ] 端到端测试

### Phase 6.3 - 环境感知

- [ ] `GET /api/vms/:id/system/snapshot`
- [ ] `GET /api/vms/:id/system/directory`
- [ ] `GET /api/vms/:id/system/app`
- [ ] `GET/POST /api/vms/:id/system/clipboard`
- [ ] `GET /api/vms/:id/system/recent-files`
- [ ] `GET /api/vms/:id/system/environment`

### Phase 6.4 - Gateway 适配

- [ ] 创建 vmcontrol_adapter.py
- [ ] 迁移所有工具调用
- [ ] 配置开关（vmuse/vmcontrol）
- [ ] 回退机制

### Phase 6.5 - 清理

- [ ] 停止 VMUSE 服务
- [ ] 删除 FastMCP 代码
- [ ] 清理 systemd 配置
- [ ] 更新 VM 镜像脚本
- [ ] 验证功能完整性

---

## 🎯 成功标准

- ✅ 所有 34 个工具功能正常
- ✅ 性能提升 2x（除浏览器）
- ✅ VM 资源减少 ~100MB
- ✅ 端到端测试通过率 > 95%
- ✅ 无生产事故

---

**最后更新**: 2026-02-06  
**状态**: 设计完成，待实施
