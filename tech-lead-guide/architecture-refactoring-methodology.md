# 架构重构方法论

> 基于 2026-02-07 多个架构问题诊断与修复的实战经验总结

## 目录

1. [问题诊断方法](#1-问题诊断方法)
2. [对比学习法](#2-对比学习法)
3. [渐进式重构策略](#3-渐进式重构策略)
4. [构建系统陷阱](#4-构建系统陷阱)
5. [用户体验优先设计](#5-用户体验优先设计)
6. [前端状态清理](#6-前端状态清理)

---

## 1. 问题诊断方法

### 系统性诊断流程

```
用户报告问题
    ↓
1. 重现问题（要求截图/操作步骤）
    ↓
2. 分层验证
   - 前端：浏览器 DevTools
   - API：curl 调用
   - 数据库：SQL 查询
   - 进程：ps/ls/nc 检查
    ↓
3. 确定问题层
   - 前端渲染/状态
   - API 响应/逻辑
   - 数据库数据/约束
   - 进程/连接/文件系统
    ↓
4. 定位具体原因
    ↓
5. 修复验证
```

### 实战案例：Browser 工具 500 错误

#### 阶段 1：重现问题

**用户报告**：
- 浏览器工具返回 500 错误
- VNC 桌面黑屏
- 错误信息："Broken pipe"

**截图收集**：
- 前端错误截图
- VNC 黑屏截图
- Execution Log 截图

#### 阶段 2：分层验证

**检查进程**：
```bash
# QEMU 是否运行
ps aux | grep qemu-system
# 结果：✅ 运行中

# Socket 是否存在
ls /tmp/novaic/*-qmp-*.sock
# 结果：✅ 存在

# vmcontrol 是否运行
curl http://localhost:8080/health
# 结果：✅ 正常
```

**检查 API**：
```bash
# 列出 VM
curl http://localhost:8080/api/vms
# 结果：✅ VM 已注册

# 测试截图
curl -X POST http://localhost:8080/api/vms/{id}/screenshot
# 结果：✅ 成功

# 测试浏览器导航
curl -X POST http://localhost:8080/api/vms/{id}/browser/navigate \
  -d '{"url": "https://example.com"}'
# 结果：❌ 500 - "ModuleNotFoundError: No module named 'playwright'"
```

**检查 VM 内部**：
```bash
# SSH 进入 VM
ssh -p 20000 ubuntu@localhost

# 检查桌面进程
ps aux | grep -E "Xorg|lightdm|xfce"
# 结果：❌ 没有桌面进程

# 检查 playwright
python3 -c "import playwright"
# 结果：✅ 交互式 shell 成功，但 vmcontrol 调用失败
```

#### 阶段 3：确定问题层

**问题 1**：VNC 黑屏
- 层级：VM 内部（桌面环境）
- 原因：lightdm 启动失败

**问题 2**：Browser 工具 500
- 层级：VM 内部（环境变量）
- 原因：vmcontrol SSH 调用时环境变量不正确

#### 阶段 4：定位具体原因

**问题 1 深挖**：
```bash
# 查看 lightdm 日志
journalctl -u lightdm -n 50
# 发现："Greeter closed communication channel"

# 结论：lightdm 配置问题，这是旧 VM 实例
```

**问题 2 深挖**：
```python
# 对比测试
# 交互式 SSH：成功
ssh -p 20000 ubuntu@localhost
$ python3 -c "import playwright"  # ✅

# vmcontrol 调用：失败
# 原因：不同的 shell 类型，环境变量加载不同
```

#### 阶段 5：修复策略

**问题 1**：重建 VM（应用最新 cloud-init）
**问题 2**：修改 vmcontrol 或使用 wrapper 脚本

---

## 2. 对比学习法

### 方法论

当遇到不稳定的组件 A 时：
1. 找到类似但稳定的组件 B
2. 对比 A 和 B 的实现差异
3. 分析为什么 B 稳定
4. 借鉴 B 的成功经验修复 A

### 实战案例：QMP vs VNC

#### 背景

- VNC 连接很稳定 ✅
- QMP 连接经常 "Broken pipe" ❌
- 两者都使用 Unix socket 连接 QEMU

#### 对比分析

**VNC 实现**（稳定）：
```rust
// 每次 WebSocket 请求都新建连接
pub async fn vnc_websocket(...) {
    let vnc_stream = UnixStream::connect(&vnc_socket).await?;
    // 双向转发
    // 连接自动关闭（Drop）
}
```

**QMP 实现**（不稳定）：
```rust
// 启动时建立，一直持有
pub struct VmManager {
    pub qmp: QmpClient,  // ❌ 长连接
}

// 所有命令都用这个连接
vm.qmp.execute("screendump", args).await?;
```

#### 关键差异表

| 对比项 | VNC | QMP |
|--------|-----|-----|
| 连接方式 | 每次新建 | 长连接 |
| 状态 | 无状态 | 有状态 |
| QEMU 重启后 | 自动恢复 | 彻底失败 |
| 错误处理 | 自动（下次重连）| 需要手动重连 |

#### 借鉴方案

**结论**：VNC 的按需连接模式是成功的关键

**修复 QMP**：
```rust
// 改为按需连接（像 VNC 一样）
pub struct VmManager {
    pub qmp_socket: String,  // ✅ 只保存路径
}

impl VmManager {
    pub async fn create_qmp_client(&self) -> Result<QmpClient> {
        QmpClient::connect(&self.qmp_socket).await  // ✅ 每次新建
    }
}
```

### 对比学习的适用场景

| 场景 | 如何对比 |
|------|---------|
| 组件不稳定 | 找到稳定的类似组件 |
| 性能问题 | 找到性能好的类似实现 |
| 用户体验差 | 找到体验好的类似功能 |
| 代码复杂 | 找到简单的类似实现 |

---

## 3. 渐进式重构策略

### 重构原则

1. **不要一次改太多** - 每次改一个问题
2. **每步都验证** - 修改后立即测试
3. **保持向后兼容** - 除非明确不需要
4. **记录决策理由** - 写清楚为什么这样改

### 实战案例：多模态标准迁移

#### 目标

统一所有截图工具的返回格式为 MCP 标准。

#### 错误的做法 ❌

```python
# 一次性修改所有地方
1. 修改 vmcontrol API
2. 修改 playwright_helper.py
3. 修改 vmuse_adapter.py
4. 修改 multimodal.py
5. 修改前端

# 结果：改完后发现很多地方都坏了，不知道哪里错了
```

#### 正确的做法 ✅

**阶段 1：基础设施准备**
```python
# 1. 先更新 multimodal.py，支持新旧两种格式
def extract_from_result(result):
    # 支持 MCP content 数组（新）
    if "content" in result:
        return _parse_content_array(result["content"])
    # 支持 data 字段（旧）
    if "data" in result:
        return _parse_legacy_data(result["data"])
```

**验证**：测试新旧格式都能识别 ✅

**阶段 2：逐个迁移工具**
```python
# 2. 先迁移 playwright_helper.py
def screenshot(...):
    return {
        "status": "success",
        "content": [  # 新格式
            {"type": "image", "data": base64_data, "mimeType": "image/png"}
        ]
    }
```

**验证**：测试 browser_screenshot 工具 ✅

**阶段 3：迁移 Gateway API**
```python
# 3. 修改 Gateway API 返回 MCP 格式
@router.post("/vms/{vm_id}/screenshot")
async def screenshot(...):
    data = await vmcontrol.screenshot(vm_id)
    return {
        "content": [
            {"type": "image", "data": data["data"], "mimeType": "image/png"}
        ]
    }
```

**验证**：测试 screenshot 工具 ✅

**阶段 4：清理旧代码**
```python
# 4. 所有工具都迁移后，移除兼容代码
def extract_from_result(result):
    # 只保留新格式
    if "content" in result:
        return _parse_content_array(result["content"])
    # 移除旧格式支持
```

### 渐进式重构 Checklist

- [ ] 制定分阶段计划
- [ ] 先做基础设施（支持新旧）
- [ ] 逐个迁移模块
- [ ] 每步都验证
- [ ] 最后清理兼容代码

---

## 4. 构建系统陷阱

### 案例：build.sh 的条件判断

#### 问题发现

**现象**：修改了 vmcontrol 源代码，但 build 后没有生效。

**诊断**：
```bash
# 检查二进制文件时间戳
ls -lh novaic-app/src-tauri/vmcontrol/target/release/vmcontrol
# 修改时间：2026-02-07 10:26 ❌ 旧的

# 检查源代码修改时间
ls -lh novaic-app/src-tauri/vmcontrol/src/main.rs
# 修改时间：2026-02-07 11:34 ✅ 新的
```

**结论**：源代码已修改，但二进制没有重新编译！

#### 根因分析

**查看 build.sh**：
```bash
# novaic-app/build.sh 第 46-51 行
if [ ! -f "target/release/vmcontrol" ]; then
    echo "  Building vmcontrol (release mode)..."
    cargo build --release
else
    echo "  vmcontrol already built"  # ❌ 跳过编译
fi
```

**问题**：
- 只检查文件是否存在
- 不检查源代码是否修改
- 导致源代码变化后不重新编译

#### 修复方案

**方案 A：总是编译**（推荐）
```bash
# 移除条件判断
echo "  Building vmcontrol (release mode)..."
cargo build --release

# Cargo 会自动增量编译，只重新编译修改的文件
```

**优点**：
- ✅ 简单可靠
- ✅ Cargo 增量编译保证效率
- ✅ 不会遗漏变更

**方案 B：基于时间戳判断**（不推荐）
```bash
# 检查源文件是否比二进制新
if [ src/main.rs -nt target/release/vmcontrol ]; then
    cargo build --release
fi
```

**缺点**：
- ❌ 需要检查所有源文件
- ❌ 容易遗漏（Cargo.toml、依赖等）
- ❌ 复杂且不可靠

### 构建系统最佳实践

1. **依赖构建工具的智能**
   - Cargo、npm、pyinstaller 都有增量编译
   - 不要自己实现缓存逻辑

2. **总是重新构建**
   ```bash
   # ✅ 简单可靠
   cargo build --release
   npm run build
   pyinstaller --clean spec.py
   ```

3. **避免条件判断**
   ```bash
   # ❌ 容易出错
   if [ ! -f output ]; then build; fi
   
   # ✅ 总是构建
   build
   ```

4. **使用 --clean 标志**
   ```bash
   # 清理旧产物，确保干净构建
   pyinstaller --clean --noconfirm spec.py
   ```

---

## 5. 用户体验优先设计

### 案例：DISPLAY 环境变量配置

#### 用户需求

**用户说**："我希望在 VNC 窗口看到 AI 在操作界面，这样用户友好。"

#### 技术现状

**问题**：不同程序使用不同的 DISPLAY

| 程序 | DISPLAY | VNC 可见性 |
|------|---------|----------|
| Playwright | `DISPLAY=:99`（Xvfb）| ❌ 不可见 |
| 其他 GUI 工具 | 未设置 | ❌ 可能不可见 |
| 主桌面 | `DISPLAY=:0` | ✅ 可见 |
| VNC | 连接到 `:0` | ✅ 可见 |

#### 用户体验分析

**当前体验**：
- 用户打开 VNC，看到黑屏或空桌面
- 浏览器在后台运行（Xvfb），看不到
- 不知道 AI 在干什么

**期望体验**：
- 用户打开 VNC，看到桌面环境
- AI 操作浏览器，用户能看到
- 感觉 AI 在"真实"的电脑上工作

#### 设计决策

**方案 A**：保持无头模式（Xvfb）
- 理由：性能好、独立显示
- 问题：用户看不到，不友好 ❌

**方案 B**：全部使用 DISPLAY=:0
- 理由：用户能看到 AI 操作，友好
- 实现：统一所有程序使用 `:0`
- 决定：✅ 采用

#### 实施方案

**修改 1：Playwright 使用真实桌面**
```rust
// 修改前：无头模式
"xvfb-run python3 playwright_helper.py"

// 修改后：真实桌面
"DISPLAY=:0 python3 playwright_helper.py"
```

**修改 2：系统默认 DISPLAY**
```yaml
# cloud-init
runcmd:
  - echo 'DISPLAY=:0' | sudo tee -a /etc/environment
```

**修改 3：所有 GUI 程序统一**
```python
# launch_app
command = f"DISPLAY=:0 nohup {app_name} {args} > /dev/null 2>&1 &"

# shell_exec
command_with_display = f"DISPLAY=:0 {command}"
```

**修改 4：移除 Xvfb**
```yaml
# cloud-init - 移除不需要的包
packages:
  # - xvfb  # ❌ 移除
```

#### 验证用户体验

**测试**：
1. 启动 VM，打开 VNC
2. 调用 browser_navigate 工具
3. 检查 VNC 中是否看到浏览器窗口打开
4. 检查浏览器是否导航到目标 URL

**结果**：✅ 用户能看到 AI 操作浏览器

### 用户体验设计原则

1. **可见性优先**
   - 让用户看到系统在做什么
   - 避免"黑盒"操作

2. **符合直觉**
   - 用户期望的行为是什么？
   - 不要因为技术方便就违背直觉

3. **实际测试**
   - 不要假设用户体验
   - 实际操作验证

4. **技术服务体验**
   - 技术方案为体验服务
   - 不是体验妥协于技术

---

## 6. 前端状态清理

### 案例：删除 Agent 后前端残留

#### 问题

用户删除了所有 agent，刷新页面后：
- 前端仍显示旧 agent 的工具调用结果
- 数据库已清空（0 条 agent）
- 后端 API 返回空列表

#### 诊断过程

**步骤 1：检查数据流**
```javascript
// 1. 前端从哪里获取 agent？
useAppStore.getState().agents  // []

// 2. 为什么还显示旧消息？
useAppStore.getState().currentAgentId  // "79b813e8-..." ❌
localStorage.getItem('novaic-current-agent-id')  // "79b813e8-..." ❌
```

**步骤 2：分析状态管理**
```typescript
// store/index.ts - loadAgents()
loadAgents: async () => {
    const response = await api.listAgents();
    set({ agents: response.agents });
    
    if (response.agents.length === 0) {
        return;  // ❌ 直接返回，不清空 currentAgentId
    }
    
    // 自动选择 agent 逻辑...
}
```

**问题**：
- API 返回空列表
- `loadAgents()` 更新了 `agents` 为 `[]`
- 但没有清空 `currentAgentId`
- localStorage 也没有清空

#### 根因

**多个状态不同步**：
| 状态 | 值 | 是否正确 |
|------|-----|---------|
| `agents` | `[]` | ✅ |
| `currentAgentId` | `"79b813e8-..."` | ❌ 残留 |
| localStorage | `"79b813e8-..."` | ❌ 残留 |
| SSE 连接 | 连接到旧 agent | ❌ 残留 |

#### 修复方案

**修改 loadAgents()**：
```typescript
loadAgents: async () => {
    const response = await api.listAgents();
    set({ agents: response.agents });
    
    // 如果 agent 列表为空，清空所有状态
    if (response.agents.length === 0) {
        console.log('[Store] No agents found, clearing state');
        set({ 
            currentAgentId: null,
            messages: [],
            logs: [],
            lastLogId: null,
            logSubagentId: null,
            logSubagents: [],
        });
        saveAgentId(null);  // 清空 localStorage
        get().disconnectSSE();  // 断开 SSE 连接
        return;
    }
    
    // 现有的 agent 选择逻辑...
}
```

**修改 App.tsx**：
```typescript
if (loadedAgents.length === 0) {
    // 清空所有状态和 localStorage
    console.log('[App] No agents found, clearing state');
    const { disconnectSSE } = useAppStore.getState();
    disconnectSSE();
    useAppStore.setState({ 
        currentAgentId: null,
        messages: [],
        logs: [],
        // ... 其他状态
    });
    localStorage.removeItem('novaic-current-agent-id');
    return;
}
```

### 前端状态清理 Checklist

删除操作后需要清理：
- [ ] 内存状态（Zustand/Redux store）
- [ ] 本地存储（localStorage/sessionStorage）
- [ ] 网络连接（WebSocket/SSE）
- [ ] 定时器（setTimeout/setInterval）
- [ ] 缓存（React Query/SWR cache）
- [ ] 事件监听器（addEventListener）

### 状态清理最佳实践

1. **集中清理逻辑**
   ```typescript
   // 创建清理函数
   const clearAgentState = () => {
       set({ currentAgentId: null, messages: [], logs: [] });
       localStorage.removeItem('novaic-current-agent-id');
       disconnectSSE();
   };
   
   // 在需要的地方调用
   if (agents.length === 0) {
       clearAgentState();
   }
   ```

2. **双重保险**
   ```typescript
   // Store 层清理
   loadAgents() { if (empty) clearState(); }
   
   // UI 层再次清理（防御性编程）
   useEffect(() => { if (empty) clearState(); }, [agents]);
   ```

3. **立即清理**
   ```typescript
   // ❌ 延迟清理
   setTimeout(() => clearState(), 1000);
   
   // ✅ 立即清理
   clearState();
   ```

4. **可观察的清理**
   ```typescript
   // 添加日志，方便调试
   console.log('[Store] Clearing agent state');
   clearState();
   console.log('[Store] State cleared');
   ```

---

## 总结：架构重构方法论

### 核心原则

1. **系统性诊断**
   - 分层验证（前端→API→数据库→进程）
   - 找到问题的真正层级
   - 不要只看表象

2. **对比学习**
   - 找到稳定的类似组件
   - 分析差异
   - 借鉴成功经验

3. **渐进式重构**
   - 不要一次改太多
   - 每步都验证
   - 保持兼容性

4. **用户体验优先**
   - 理解用户期望
   - 技术服务体验
   - 实际验证

5. **简单胜过复杂**
   - 按需连接 > 长连接 + 重连
   - 总是编译 > 条件判断
   - 数据库级联 > 应用层管理

### 诊断流程模板

```
1. 重现问题
   - 要求截图/操作步骤
   - 确认问题表现
   
2. 分层验证
   - 前端：DevTools、Store
   - API：curl 调用
   - 数据库：SQL 查询
   - 进程：ps/ls/nc
   
3. 确定问题层
   - 定位到具体层级
   - 找到问题组件
   
4. 对比分析
   - 找到类似的稳定组件
   - 分析差异
   
5. 制定方案
   - 渐进式计划
   - 分阶段实施
   
6. 修复验证
   - 每步都测试
   - 确认问题解决
```

### 常见陷阱

| 陷阱 | 后果 | 避免方法 |
|------|------|---------|
| 只看表象 | 治标不治本 | 分层验证 |
| 一次改太多 | 改坏了不知道哪错 | 渐进式重构 |
| 过度优化 | 增加复杂度 | 简单优先 |
| 忽略用户体验 | 功能能用但难用 | 用户视角 |
| 条件构建 | 遗漏变更 | 总是重新构建 |
| 状态不清理 | 残留数据 | Checklist |

---

*最后更新：2026-02-07*
*基于多个架构问题诊断与修复的实战经验*
