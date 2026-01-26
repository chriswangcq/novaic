# NovAIC - The AI Computer

> "不是临时沙箱，而是你的 AI 专属电脑 —— 它记得你、理解你、为你持续工作。"
> 
> "PC 是给人用的电脑，AIC 是给 AI 用的电脑。NovAIC 是 AI 时代的新开始。"

---

## 📋 目录

1. [愿景与定位](#愿景与定位)
2. [核心差异化](#核心差异化)
3. [产品架构](#产品架构)
4. [重命名计划](#重命名计划)
5. [技术路线图](#技术路线图)
6. [商业模式](#商业模式)
7. [执行计划](#执行计划)

---

## 愿景与定位

### 品牌释义

```
NovAIC = Nov(a) + AIC

Nova  = 超新星，象征 AI 时代的新开始
AIC   = AI Computer，给 AI 用的电脑

发音：/ˈnoʊveɪk/ (诺维克)
```

### 一句话定义

**NovAIC 是一个开源的、持久化的 AI 电脑操作平台，让 AI 像人一样拥有自己的电脑。**

### 核心理念

```
传统 AI 工具：        NovAIC：
┌─────────────┐      ┌─────────────┐
│  无状态     │      │  有状态     │
│  临时执行   │      │  持久运行   │
│  用完即弃   │      │  记忆延续   │
│  仅能聊天   │      │  真正做事   │
└─────────────┘      └─────────────┘
```

### 目标用户

| 用户群 | 需求 | NovAIC 价值 |
|--------|------|-----------|
| **个人开发者** | AI 助手帮忙写代码、测试、部署 | 持久化开发环境 |
| **知识工作者** | AI 帮忙处理邮件、文档、数据 | 自动化日常任务 |
| **小型企业** | 低成本自动化运营 | 替代部分人力 |
| **AI 应用开发者** | 构建 AI Agent 应用 | 开源可定制的基础设施 |

### 与竞品的定位差异

```
市场格局：

                    云端托管
                       ↑
                       │
    E2B ────────────── │ ────────────── Anthropic
    (代码沙箱)         │               Computer Use
                       │               (闭源云服务)
                       │
    临时/无状态 ←──────┼──────→ 持久/有状态
                       │
                       │
    Replit ─────────── │ ────────────── NovAIC ⭐
    (开发环境)         │               (AI Computer)
                       │
                       ↓
                    本地部署

NovAIC 占据：本地部署 + 持久有状态 的独特位置
```

---

## 核心差异化

### 1. 持久化 (Persistence)

**问题**：现有方案（E2B、临时沙箱）每次会话都是全新环境

**NovAIC 方案**：
- QEMU + QCOW2 磁盘，完整保存系统状态
- 关机后所有数据、配置、登录状态保留
- 支持快照、回滚、增量备份

```
用户体验对比：

E2B/临时沙箱：
  Session 1: 安装微信 → 登录 → 配置
  Session 2: 重新安装 → 重新登录 → 重新配置 😫
  
NovAIC：
  Day 1: 安装微信 → 登录 → 配置
  Day 2: 直接使用，一切都在 ✅
  Day 30: 还是登录状态，配置完好 ✅
```

### 2. 记忆系统 (Memory)

**问题**：AI 没有长期记忆，每次对话都要重新理解上下文

**NovAIC 方案**：
- `memory_save/recall` - 持久化键值存储
- `goal_set/progress` - 多步骤任务跟踪
- `session_state` - 会话状态管理
- 数据存储在 `~/.novaic/memory/`，重启不丢失

```python
# AI 可以这样使用记忆：
memory_save("project_context", {
    "name": "电商后台",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    "current_task": "实现用户认证模块",
    "progress": "已完成数据库设计，正在写 API"
})

# 下次对话，AI 可以回忆：
context = memory_recall("project_context")
# AI 立即知道项目背景，无需重复解释
```

### 3. 环境感知 (Context Awareness)

**问题**：AI 不了解当前系统状态，需要反复询问

**NovAIC 方案**：
- `system_snapshot` - 一键获取系统全貌
- `directory_snapshot` - 智能分析项目结构
- `app_state` - 应用运行状态
- `environment_info` - 开发环境信息

```json
// system_snapshot 返回示例：
{
  "system": {"hostname": "novaic-vm", "user": "ubuntu"},
  "desktop": {
    "windows": [{"title": "VSCode - project"}, {"title": "Chrome"}],
    "clipboard": "复制的内容..."
  },
  "resources": {
    "memory": {"total": "4GB", "available": "2.5GB"},
    "disk": {"total": "40GB", "available": "30GB"}
  }
}
```

### 4. 完整桌面能力 (Full Desktop)

**问题**：大多数方案只能执行代码，无法操作 GUI 应用

**NovAIC 方案**：
- 完整 Ubuntu 桌面 (XFCE)
- VNC 远程访问
- 44 个 MCP 工具覆盖：截图、鼠标、键盘、窗口管理
- 可以操作任何 Linux GUI 应用（微信、浏览器、IDE...）

```
已验证的能力：
✅ 下载安装微信 Linux 版
✅ 扫码登录微信
✅ 给联系人发送消息
✅ 浏览器自动化
✅ 文件管理
✅ 命令行操作
```

### 5. 开源自托管 (Open Source & Self-hosted)

**问题**：商业方案数据上云、成本高、不可控

**NovAIC 方案**：
- 完全开源 (MIT License)
- 本地部署，数据不出本机
- 零云端依赖
- 可接入任意 LLM（Claude、GPT、本地模型）

---

## 产品架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    NovAIC Platform                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │NovAIC App   │  │ NovAIC Web  │  │ NovAIC CLI  │         │
│  │  (Tauri)    │  │  (React)    │  │  (Python)   │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  NovAIC Agent                        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ Planner │  │Executor │  │ Memory  │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  NovAIC Core                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│  │  │ Desktop │  │ Browser │  │  Shell  │  │ Files  │ │   │
│  │  │  Tools  │  │  Tools  │  │  Tools  │  │ Tools  │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │   │
│  │  │ Window  │  │ Memory  │  │ Context │  │ Result │ │   │
│  │  │  Tools  │  │  Tools  │  │  Tools  │  │ Cache  │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └────────┘ │   │
│  │                    MCP Server (44 Tools)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 NovAIC Runtime                       │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │  Ubuntu 24.04 VM (QEMU/KVM)                 │   │   │
│  │  │  ├── XFCE Desktop                           │   │   │
│  │  │  ├── VNC Server (:5901)                     │   │   │
│  │  │  ├── SSH Server (:22)                       │   │   │
│  │  │  ├── MCP Server (:8080)                     │   │   │
│  │  │  └── Persistent Disk (QCOW2)                │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 职责 | 技术栈 |
|------|------|--------|
| **NovAIC App** | 桌面客户端，VNC 查看器 | Tauri + React |
| **NovAIC Web** | Web 控制台 | React + Vite |
| **NovAIC CLI** | 命令行工具 | Python |
| **NovAIC Agent** | AI 智能体框架 | Python + LangChain |
| **NovAIC Core** | MCP 工具服务器 | Python + FastAPI |
| **NovAIC Runtime** | VM 运行时环境 | QEMU + Ubuntu |

### 端口规划

| 端口 | 服务 | 说明 |
|------|------|------|
| 8080 | NovAIC Core MCP | VM 内部 |
| 8081 | NovAIC Core MCP | 宿主机映射 |
| 5901 | VNC Server | VM 内部 |
| 5900 | VNC Proxy | 宿主机映射 |
| 2222 | SSH | 宿主机映射 |
| 6080 | noVNC (可选) | Web VNC |

---

## 重命名计划

### 目录结构变更

```
当前结构 (novaic/)              目标结构 (novaic/)
├── agent/                     ├── packages/
├── app/                       │   ├── novaic-core/      # 原 linux2mcp
├── cloud/                     │   │   ├── src/novaic_core/
├── executor/                  │   │   │   ├── tools/
├── linux2mcp/  ────────────→  │   │   │   ├── memory/
│   └── src/linux2mcp/         │   │   │   ├── context/
├── vm/                        │   │   │   └── main.py
└── docs/                      │   │   └── pyproject.toml
                               │   │
                               │   ├── novaic-agent/     # 原 agent
                               │   │   └── src/novaic_agent/
                               │   │
                               │   ├── novaic-app/       # 原 app
                               │   │   └── src/
                               │   │
                               │   └── novaic-cloud/     # 原 cloud
                               │       └── src/
                               │
                               ├── runtime/              # 原 vm
                               │   ├── qemu/
                               │   ├── scripts/
                               │   └── images/
                               │
                               ├── docs/
                               │   ├── getting-started.md
                               │   ├── architecture.md
                               │   └── api-reference.md
                               │
                               ├── examples/
                               │   ├── send-wechat.py
                               │   ├── web-automation.py
                               │   └── file-organizer.py
                               │
                               ├── README.md
                               ├── LICENSE
                               ├── CONTRIBUTING.md
                               └── ROADMAP.md
```

### 包命名变更

| 当前 | 目标 | PyPI 包名 |
|------|------|-----------|
| linux2mcp | novaic-core | `novaic` |
| agent | novaic-agent | `novaic-agent` |
| cloud | novaic-cloud | `novaic-cloud` |

### 代码重命名清单

```python
# 1. Python 包名
linux2mcp → novaic_core
from linux2mcp import ... → from novaic_core import ...

# 2. 类名
Linux2MCP → NovAICCore
MCP_TOOLS → NOVAIC_TOOLS

# 3. 配置文件
~/.linux2mcp/ → ~/.novaic/
/opt/linux2mcp/ → /opt/novaic/

# 4. 服务名
linux2mcp.service → novaic-core.service

# 5. Docker/容器
linux2mcp:latest → novaic-core:latest
```

### 执行步骤

```bash
# Step 1: 创建新目录结构
mkdir -p novaic/packages/{novaic-core,novaic-agent,novaic-app,novaic-cloud}
mkdir -p novaic/{runtime,docs,examples}

# Step 2: 移动并重命名文件
mv linux2mcp/src/linux2mcp novaic/packages/novaic-core/src/novaic_core
mv agent novaic/packages/novaic-agent
mv app novaic/packages/novaic-app
mv cloud novaic/packages/novaic-cloud
mv vm novaic/runtime

# Step 3: 更新 import 语句
find novaic -name "*.py" -exec sed -i 's/linux2mcp/novaic_core/g' {} \;
find novaic -name "*.py" -exec sed -i 's/from linux2mcp/from novaic_core/g' {} \;

# Step 4: 更新配置文件
# pyproject.toml, package.json, Cargo.toml 等

# Step 5: 更新文档
# README.md, docs/*.md
```

---

## 技术路线图

### Phase 1: 核心完善 (当前 → 2026 Q1)

**目标**：让 NovAIC Core 稳定可用

| 任务 | 状态 | 优先级 |
|------|------|--------|
| 44 个 MCP 工具 | ✅ 完成 | - |
| 记忆系统 | ✅ 完成 | - |
| 环境感知 | ✅ 完成 | - |
| 结果缓存与分段查询 | ✅ 完成 | - |
| 图片正确返回 | ✅ 完成 | - |
| OCR 文字识别 | 🔲 待做 | P0 |
| Vision 视觉理解 | 🔲 待做 | P0 |
| 错误恢复机制 | 🔲 待做 | P1 |
| 性能优化 | 🔲 待做 | P1 |
| 单元测试 | 🔲 待做 | P1 |

### Phase 2: 产品化 (2026 Q2)

**目标**：可供他人使用的产品

| 任务 | 说明 |
|------|------|
| 重命名为 NovAIC | 目录结构、包名、品牌 |
| NovAIC App 完善 | VNC 集成、状态显示 |
| 一键安装脚本 | `curl -fsSL https://novaic.dev/install.sh | sh` |
| 完善文档 | 快速开始、API 参考、示例 |
| GitHub 开源 | README、LICENSE、CONTRIBUTING |
| 演示视频 | 微信发消息、自动化任务 |

### Phase 3: 智能化 (2026 Q3)

**目标**：更智能的 AI Agent

| 任务 | 说明 |
|------|------|
| NovAIC Agent 框架 | 规划-执行-反思循环 |
| 多步骤任务编排 | Workflow DSL |
| 自然语言编程 | "帮我每天早上发微信问好" |
| 任务模板 | 预置常用自动化任务 |
| 错误自动修复 | AI 自动处理异常 |

### Phase 4: 生态化 (2026 Q4)

**目标**：可持续的商业模式

| 任务 | 说明 |
|------|------|
| NovAIC Cloud | 托管服务，按需付费 |
| 企业版 | 多用户、审计日志、SSO |
| 插件市场 | 社区贡献的工具和模板 |
| API 开放 | 第三方集成 |

---

## 商业模式

### 收入来源

```
┌─────────────────────────────────────────────────────────────┐
│                   NovAIC 商业模式                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  开源核心 (NovAIC Core)                                      │
│  ├── 完全免费                                                │
│  ├── MIT License                                            │
│  └── 社区驱动                                                │
│                                                             │
│  增值服务                                                    │
│  ├── NovAIC Cloud                                           │
│  │   ├── 托管 VM 实例                                       │
│  │   ├── 按小时计费: $0.05/hour                             │
│  │   └── 月付套餐: $20/month (720 hours)                    │
│  │                                                          │
│  ├── NovAIC Enterprise                                      │
│  │   ├── 多用户管理                                         │
│  │   ├── 审计日志                                           │
│  │   ├── SSO 集成                                           │
│  │   ├── 优先支持                                           │
│  │   └── 定价: $500/month 起                                │
│  │                                                          │
│  ├── 技术支持                                               │
│  │   ├── 部署咨询                                           │
│  │   ├── 定制开发                                           │
│  │   └── 培训服务                                           │
│  │                                                          │
│  └── 插件市场 (未来)                                        │
│      └── 收取 20% 佣金                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 收入预测 (保守)

| 年份 | ARR | 说明 |
|------|-----|------|
| Year 1 | $0 | 打磨产品、建立社区 |
| Year 2 | $200K | 早期付费用户 |
| Year 3 | $1M | 产品市场契合 |
| Year 4 | $5M | 规模化增长 |
| Year 5 | $15M+ | 市场领导者 |

### 融资策略

```
阶段 1: 自举 (Bootstrapping)
├── 不融资
├── 业余时间开发
├── 目标: 1000 GitHub Stars, 100 活跃用户
└── 时间: 6-12 个月

阶段 2: 种子轮 (可选)
├── 融资: $500K - $1M
├── 用途: 全职开发、市场推广
├── 目标: 10K Stars, 1000 付费用户
└── 估值: $5M - $10M

阶段 3: A 轮 (如果需要)
├── 融资: $3M - $5M
├── 用途: 团队扩张、产品矩阵
├── 目标: $1M ARR
└── 估值: $20M - $30M
```

---

## 执行计划

### 立即行动 (本周)

- [ ] 完成 OCR 工具集成
- [ ] 完成目录重命名脚本
- [ ] 更新 README.md
- [ ] 创建 novaic-vision.md (本文档)

### 短期目标 (1 个月)

- [ ] 完成 NovAIC 重命名
- [ ] 发布 v0.1.0
- [ ] 写 3 篇技术博客
- [ ] 录制演示视频
- [ ] 提交 Hacker News / Product Hunt

### 中期目标 (3 个月)

- [ ] 1000 GitHub Stars
- [ ] 100 活跃用户
- [ ] 完善文档和示例
- [ ] 建立 Discord 社区
- [ ] 收集用户反馈

### 长期目标 (1 年)

- [ ] 10K GitHub Stars
- [ ] 1000 付费用户
- [ ] $200K ARR
- [ ] 决定是否全职投入

---

## 附录

### A. 技术栈总览

| 层级 | 技术 |
|------|------|
| 前端 | React, TypeScript, Tailwind CSS |
| 桌面 | Tauri (Rust) |
| 后端 | Python, FastAPI, Uvicorn |
| AI | LangChain, OpenAI/Anthropic API |
| 虚拟化 | QEMU/KVM, QCOW2 |
| 操作系统 | Ubuntu 24.04 LTS |
| 桌面环境 | XFCE4 |
| 远程访问 | VNC (TigerVNC), SSH |
| 浏览器自动化 | Playwright |
| 协议 | MCP (Model Context Protocol) |

### B. 相关链接

- GitHub: github.com/novaic (待创建)
- 文档: docs.novaic.dev (待创建)
- Discord: discord.gg/novaic (待创建)
- Twitter: @novaic_ai (待创建)

### C. 联系方式

- 作者: (你的名字)
- Email: (你的邮箱)
- Twitter: (你的 Twitter)

---

*最后更新: 2026-01-23*
