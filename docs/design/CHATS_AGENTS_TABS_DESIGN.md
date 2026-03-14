# Chats / Agents Tab 拆分设计

> 目标：新增 Chats tab（聊天列表 + 聊天内容），原 Agents tab 改为（代理列表 + agent tools 配置）。

---

## 一、现状

### 1.1 当前主导航

| Tab | 第二栏 | 第三栏 |
|-----|--------|--------|
| **Agents** | Agents 列表 | 选中 agent → ChatPanel（聊天） |
| **Devices** | Devices 列表 | DeviceManagerPage（VNC 等） |
| **Setting** | Settings 一级列表 | SettingsModal 二级内容 |

### 1.2 问题

- Agents tab 同时承担「选 agent 聊天」和「配置 agent」两个场景
- 用户想聊天时要点 Agents，想配置 tools 时也点 Agents，入口混在一起
- 缺少独立的「聊天」入口（类似微信的会话列表）

---

## 二、目标设计

### 2.1 主导航变更

| Tab | 第二栏 | 第三栏 |
|-----|--------|--------|
| **Chats**（新增） | 聊天列表（会话列表） | 选中会话 → ChatPanel（聊天内容） |
| **Agents**（重构） | Agents 列表 | 选中 agent → AgentToolsTab（配置 tools、skills、设备绑定等） |
| **Devices** | Devices 列表 | DeviceManagerPage |
| **Setting** | Settings 一级列表 | SettingsModal 二级内容 |

### 2.2 职责划分

| Tab | 用途 | 第二栏 | 第三栏 |
|-----|------|--------|--------|
| **Chats** | 与 AI 对话 | 会话列表（每个 agent 一个会话，展示最后一条消息预览） | 聊天界面（Header + ChatPanel） |
| **Agents** | 配置代理 | Agent 列表 | AgentToolsTab（tools、skills、bootstrap、设备绑定等） |

### 2.3 数据关系

- 当前：1 agent = 1 conversation（一一对应）
- Chats 列表：可复用 agents 数据，每项 = agent + lastMessage
- Agents 列表：与现有一致，选中后进入配置

---

## 三、具体实现方案

### 3.1 PrimaryNav / BottomTabBar

- 新增 `chats` tab，图标用 `MessageCircle` 或 `MessagesSquare`
- Tab 顺序：`chats` | `agents` | `devices` | `setting`
- `PrimaryTab` 类型：`'chats' | 'agents' | 'devices' | 'setting'`

### 3.2 AgentDrawer（第二栏）

**当前**：`primaryTab` 控制显示 `agentsContent` | `devicesContent` | `settingsContent`

**变更**：

- 新增 `chatsContent`：聊天列表（与 agentsContent 类似，但强调「会话」语义）
  - 列表项：agent 头像、名称、最后一条消息预览
  - 点击 → `onSelectChat(agentId)`，进入第三栏 ChatPanel
- `agentsContent` 保留：Agent 列表，点击 → `onSelectAgent(agentId)`，进入第三栏 AgentToolsTab
- `primaryTab === 'chats'` 时显示 `chatsContent`
- `primaryTab === 'agents'` 时显示 `agentsContent`

**chatsContent 与 agentsContent 的差异**：

- 视觉：可共用同一列表 UI，或 Chats 用「消息气泡」风格、Agents 用「齿轮/配置」暗示
- 回调：Chats → `onSelectChat` → 第三栏 ChatPanel；Agents → `onSelectAgent` → 第三栏 AgentToolsTab

### 3.3 LayoutContainer（第三栏）

**当前**：`activeView === 'chat'` 时渲染 `Header + ChatPanel`；`activeView === 'devices'` 时渲染 `DeviceManagerPage`

**变更**：

- 引入 `activeView`：`'chats' | 'agents' | 'devices'`
- `primaryTab === 'chats'` 且选中会话 → `Header + ChatPanel`
- `primaryTab === 'agents'` 且选中 agent → `AgentToolsPanel`（封装 AgentToolsTab）
- `primaryTab === 'devices'` → `DeviceManagerPage`（不变）

**AgentToolsPanel**：

- 新建组件或复用 SettingsModal 的 `AgentToolsTab`
- 可嵌入模式：只渲染 AgentToolsTab 内容，带返回按钮
- 或：在第三栏直接渲染 `SettingsModal` 的 `embeddedMode="content"` + `embeddedTab="agent-tools"`，并传入 `selectedAgentId`

### 3.4 状态流

```
Chats tab:
  第二栏点击会话(agent) → setCurrentAgentId(agentId) + onNarrowPageChange('chat')
  第三栏 → Header + ChatPanel（与现有一致）

Agents tab:
  第二栏点击 agent → setCurrentAgentId(agentId) + onNarrowPageChange('agents')
  第三栏 → AgentToolsPanel(agentId)
```

### 3.5 手机式布局

- 手机式：第二栏 overlay，第三栏全屏
- Chats：第二栏 = 聊天列表，第三栏 = 聊天
- Agents：第二栏 = agents 列表，第三栏 = agent tools
- 底 tab 增加 Chats，顺序与 PC 一致

---

## 四、文件改动清单

| 文件 | 改动 |
|------|------|
| `PrimaryNav.tsx` | 新增 chats tab，`PrimaryTab` 扩展为 4 个 |
| `BottomTabBar.tsx` | 同上 |
| `LayoutContainer.tsx` | `activeView` 扩展；chats/agents 分支渲染不同第三栏 |
| `AgentDrawer.tsx` | 新增 `chatsContent`；`primaryTab === 'chats'` 时显示；`onSelectChat` 回调 |
| `SettingsModal.tsx` | 抽取 `AgentToolsTab` 为可独立嵌入，或新增 `AgentToolsPanel` 包装 |
| 新建 `AgentToolsPanel.tsx` | 可选：封装 AgentToolsTab，接收 `agentId`，支持返回 |

---

## 五、UI 草图

### Chats tab

```
┌─────────────┬──────────────────────────────────────────────────────────┐
│  Chats      │  会话名 · 最后消息                    [Header]            │
│  ─────────  │  ─────────────────────────────────────────────────────── │
│  ○ Agent A  │                                                           │
│    最后一句… │                     ChatPanel                            │
│  ● Agent B  │                     （消息列表 + 输入框）                  │
│    最后一句… │                                                           │
│  ○ Agent C  │                                                           │
│    最后一句… │                                                           │
└─────────────┴──────────────────────────────────────────────────────────┘
```

### Agents tab

```
┌─────────────┬──────────────────────────────────────────────────────────┐
│  Agents     │  Agent B · 配置                      [返回]              │
│  ─────────  │  ─────────────────────────────────────────────────────── │
│  ○ Agent A  │                                                           │
│  ● Agent B  │              AgentToolsTab                                │
│  ○ Agent C  │              （Tools、Skills、设备绑定、Bootstrap…）       │
│  + 新建     │                                                           │
└─────────────┴──────────────────────────────────────────────────────────┘
```

---

## 六、兼容与迁移

- `currentAgentId` 在 Chats 和 Agents 间共享：在 Chats 选中的 agent 即当前聊天对象；在 Agents 选中的即当前配置对象
- 若 Chats 与 Agents 选中同一 agent，行为一致
- Setting 中的 `agent-tools` 可保留（全局入口），或改为跳转到 Agents tab 并选中对应 agent

---

## 七、可选优化

1. **Chats 列表**：未来若支持「一个 agent 多个会话」，可扩展为真正的 conversation 列表
2. **Agents 列表**：可增加「快捷进入聊天」入口（如行内图标），跳转到 Chats 并选中该 agent
3. **默认 tab**：应用启动时默认进入 Chats（用户更常聊天）还是 Agents，可配置
